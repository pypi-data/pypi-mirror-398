# Concrete subclass of Data which implements a Pandas data source

from csv import QUOTE_MINIMAL
from gzip import BadGzipFile
from typing import Any, Dict, Optional, Tuple

import numpy as np
from causaliq_core.utils import FileFormatError, is_valid_path, rndsf
from causaliq_core.utils.timing import Timing
from numpy import array
from pandas import DataFrame, crosstab, read_csv, to_numeric
from pandas.errors import EmptyDataError

from causaliq_data.data import Data, DatasetType


class Pandas(Data):
    """Data subclass which holds data in a Pandas dataframe.

    Args:
        df: Data provided as a Pandas dataframe.

    Attributes:
        df: Original Pandas dataframe providing data.
        dstype: Type of dataset (categorical/numeric/mixed).
    """

    def __init__(self, df: DataFrame) -> None:
        if not isinstance(df, DataFrame):
            raise TypeError("Pandas() bad arg type")

        if len(df) < 2 or len(df.columns) < 2:
            raise ValueError("Pandas() bad dataframe size")

        if df.isna().any().any():
            raise ValueError("Pandas() missing data unsupported")

        self._sample = self.df = df  # all refer to same object initially
        self._nodes = tuple(df.columns)
        self.order = tuple(i for i in range(len(self.nodes)))
        self.ext_to_orig = {n: n for n in self.nodes}
        self.orig_to_ext = {n: n for n in self.nodes}
        self._N = len(df)
        self._node_values = {
            c: dict(self.sample[c].value_counts())
            for c in self.sample.columns
            if self.sample[c].dtype.__str__() == "category"
        }

        # Determine node types and overall dataset type
        self._node_types = {
            n: self.sample[n].dtype.__str__() for n in self.nodes
        }
        self._set_dstype()

    @classmethod
    def _set_type(cls, column: Any) -> Any:
        """Set appropriate variable type for structure learning.

        - integers are set to category if they would fit into
          int8 otherwise minimum length integer type
        - floats set to minimum length float type
        - everything else set to category

        Args:
            column: Column to set type for.
        """
        type_name = "category"
        try:
            type_name = to_numeric(column).dtype.__str__()
            if type_name == "int64":
                type_name = to_numeric(
                    column, downcast="integer"
                ).dtype.__str__()
                type_name = "category" if type_name == "int8" else type_name
            else:
                type_name = to_numeric(
                    column, downcast="float"
                ).dtype.__str__()
        except ValueError:
            pass

        print("Variable {} set to type {}".format(column.name, type_name))
        return column.astype(str).astype(type_name)

    @classmethod
    def read(
        cls,
        filename: str,
        dstype: Optional[Any] = None,
        N: Optional[int] = None,
    ) -> "Pandas":
        """Read a file into a Pandas object.

        Args:
            filename: Full path of data file.
            dstype: Type of dataset.
            N: Number of rows to read.

        Returns:
            Data contained in file.

        Raises:
            TypeError: If argument types incorrect.
            ValueError: If illegal value coercion or N < 2.
            FileNotFoundError: If file does not exist.
            FileFormatError: If format of file incorrect.
        """
        if (
            not isinstance(filename, str)
            or (
                N is not None
                and (not isinstance(N, int) or isinstance(N, bool))
            )
            or (
                dstype is not None
                and (
                    not isinstance(dstype, (DatasetType, str))
                    or dstype not in {v for v in DatasetType}
                )
            )
        ):
            raise TypeError("Bad argument types for Pandas.read")
        if N is not None and N < 2:
            raise ValueError("Bad argument values for Pandas.read")

        is_valid_path(filename)

        try:
            # Read from file treating all values as strings initially

            dtype = (
                "float32"
                if dstype == "continuous"
                else ("category" if dstype == "categorical" else "object")
            )
            df = read_csv(
                filename,
                sep=",",
                header=0,
                encoding="utf-8",
                keep_default_na=False,
                na_values="<NA>",
                dtype=dtype,
                nrows=N,
            )
            if N is not None and N > len(df):
                raise ValueError("Bad argument values for Pandas.read")

            # Convert values to appropriate type for structure learning
            # if dstype was unspecified or was mixed

            if dstype not in {"categorical", "continuous"}:
                print()
                for col in df.columns:
                    df[col] = cls._set_type(df[col])

            return Pandas(df=df)

        except (
            UnicodeDecodeError,
            PermissionError,
            EmptyDataError,
            BadGzipFile,
        ) as e:
            raise FileFormatError("File format error: {}".format(e))

    # BNFit interface properties - expose instance variables as properties

    @property
    def nodes(self) -> Tuple[str, ...]:
        """Return the nodes in the network."""
        return self._nodes

    @nodes.setter
    def nodes(self, value: Tuple[str, ...]) -> None:
        """Set the nodes in the network."""
        self._nodes = value

    @property
    def sample(self) -> DataFrame:
        """Access to underlying data sample."""
        return self._sample

    @sample.setter
    def sample(self, value: DataFrame) -> None:
        """Set the underlying data sample."""
        self._sample = value

    @property
    def N(self) -> int:
        """Return the current sample size."""
        return self._N

    @N.setter
    def N(self, value: int) -> None:
        """Set the current sample size."""
        self._N = value

    @property
    def node_values(self) -> Dict[str, Dict]:
        """Return node values for categorical variables."""
        return self._node_values

    @node_values.setter
    def node_values(self, value: Dict[str, Dict]) -> None:
        """Set node values for categorical variables."""
        self._node_values = value

    @property
    def node_types(self) -> Dict[str, str]:
        """Return the types of all nodes."""
        return self._node_types

    @node_types.setter
    def node_types(self, value: Dict[str, str]) -> None:
        """Set the node types."""
        self._node_types = value

    def write(
        self,
        filename: str,
        compress: bool = False,
        sf: int = 10,
        zero: Optional[float] = None,
        preserve: bool = True,
    ) -> None:
        """Write data into a gzipped CSV data format file.

        Args:
            filename: Full path of data file.
            compress: Whether to gzip compress the file.
            sf: Number of s.f. to retain for numeric values.
            zero: Abs values below this counted as zero.
            preserve: Whether self.df is left unchanged by this function,
                False conserves memory if writing out large files.

        Raises:
            TypeError: If argument types incorrect.
            ValueError: If data has no columns defined.
            FileNotFoundError: If destination folder does not exist.
        """
        if (
            not isinstance(filename, str)
            or not isinstance(compress, bool)
            or not isinstance(sf, int)
            or isinstance(sf, bool)
            or (zero is not None and not isinstance(zero, float))
            or not isinstance(preserve, bool)
        ):
            raise TypeError("Bad argument types for data.write")
        zero = zero if zero is not None else 10 ** (-sf)

        if sf < 2 or sf > 10 or zero < 1e-20 or zero > 0.1:
            raise ValueError("Bad argument types for data.write")

        df = self.df.copy() if preserve is True else self.df
        for col in df.columns:
            if df[col].dtype in ["float32", "float64"]:
                df[col] = df[col].apply(lambda x: rndsf(x, sf, zero))

        try:
            df.to_csv(
                filename,
                index=False,
                na_rep="*",
                quoting=QUOTE_MINIMAL,
                escapechar="+",
                compression="gzip" if compress is True else "infer",
            )
        except OSError:
            raise FileNotFoundError("Pandas.write() failed")

    def _update_sample(
        self,
        old_N: Optional[int] = None,
        old_ext_to_orig: Optional[Dict] = None,
    ) -> None:
        """Update sample dataframe and node_values.

        Updates so they have correct sizes, node order and node names.

        Args:
            old_N: Old value of sample size if changed.
            old_ext_to_orig: Old name mapping if changed.
        """
        node_order = [self.nodes[i] for i in self.order]

        # This next line uses a possibly inefficient, but the originally used.
        # method to get a subset of rows by converting the DataFrame to a dict
        # and back to a DataFrame. The commented out line below would seem to
        # be more efficient and should produce the same result but seems to
        # result in different scores being produced at low sample sizes.

        self.sample = DataFrame(self.df[: self.N].to_dict())[
            node_order
        ]  # type: ignore[assignment]
        # self.sample = ((self.df[:self.N])[node_order])

        self.sample.rename(columns=self.orig_to_ext, inplace=True)

        if old_N is not None and old_N != self.N:

            # if N has changed then must recount node values

            self.node_values = {
                c: dict(self.sample[c].value_counts())
                for c in self.sample.columns
            }

        elif old_ext_to_orig is not None:

            # if nodes renamed then must update key values in node_values
            # and node_types

            old_rev_map = {orig: ext for ext, orig in old_ext_to_orig.items()}
            old_to_new = {
                old_rev_map[orig]: self.orig_to_ext[orig]
                for orig in self.orig_to_ext
            }
            self.node_values = {
                old_to_new[old]: counts
                for old, counts in self.node_values.items()
            }
            self.node_types = {
                old_to_new[old]: _type
                for old, _type in self.node_types.items()
            }

    def set_N(
        self,
        N: int,
        seed: Optional[int] = None,
        random_selection: bool = False,
    ) -> None:
        """Set current working sample size,
        and optionally randomise the row order.

        Args:
            N: Current working sample size.
            seed: Seed for row order randomisation if required.
            random_selection: Whether rows selected is also randomised.

        Raises:
            TypeError: If bad argument type.
            ValueError: If bad argument value.
        """
        if (
            not isinstance(N, int)
            or isinstance(N, bool)
            or not isinstance(random_selection, bool)
            or seed is not None
            and (not isinstance(seed, int) or isinstance(seed, bool))
        ):
            raise TypeError("Data.set_N() bad arg type")

        if (
            N < 1
            or N > len(self.df)
            or random_selection is True
            or (seed is not None and (seed < 0 or seed > 100))
        ):
            raise ValueError("Pandas.set_N() bad arg value")

        old_N = self.N
        self.N = N
        self._update_sample(old_N=old_N)

        if seed is not None and seed != 0:
            self.sample = self.sample.sample(
                frac=1.0, random_state=seed
            ).reset_index(drop=True)

    def randomise_names(self, seed: Optional[int] = None) -> None:
        """Randomise the node names that the learning algorithm uses.

        Allows sensitivity to these names to be assessed.

        Args:
            seed: Randomisation seed. If None, names revert back to
                original names.

        Raises:
            TypeError: For bad argument types.
            ValueError: For bad argument values.
        """
        if seed is not None and not isinstance(seed, int):
            raise TypeError("Data.randomise_names() bad arg type")

        # Revert node names back to originals

        old_ext_to_orig = self.ext_to_orig
        self.df.rename(columns=self.ext_to_orig, inplace=True)
        self.ext_to_orig = {n: n for n in self.nodes}

        # Generate the new column names

        self._generate_random_names(seed)

        # Update the Pandas sample dataset with the new column names

        self._update_sample(old_ext_to_orig=old_ext_to_orig)

    def marginals(
        self, node: str, parents: Dict, values_reqd: bool = False
    ) -> Tuple:
        """Return marginal counts for a node and its parents.

        Args:
            node: Node for which marginals required.
            parents: {node: [parents]} parents of non-orphan nodes.
            values_reqd: Whether parent and child values required.

        Returns:
            Tuple of counts, and optionally, values:
            - ndarray counts: 2D, rows=child, cols=parents
            - int maxcol: Maximum number of parental values
            - tuple rowval: Child values for each row
            - tuple colval: Parent combo (dict) for each col

        Raises:
            TypeError: For bad argument types.
        """
        if (
            not isinstance(node, str)
            or not isinstance(parents, dict)
            or not all([isinstance(p, list) for p in parents.values()])
            or not isinstance(values_reqd, bool)
        ):
            raise TypeError("Pandas.marginals() bad arg type")

        maxcol = 1
        rowval = None
        colval = None
        start = Timing.now()

        if node in parents:

            # Node has parents so get cross tabulation

            marginals = DataFrame.copy(
                crosstab(
                    self.sample[node],
                    [self.sample[p] for p in sorted(parents[node])],
                )
            )

            # max number of parental value combos is geometric product of
            # number of states of each parent

            for p in parents[node]:
                maxcol *= len(self.node_values[p].keys())

            # sort rows and columns by values to get consistent ordering

            marginals.sort_index(axis="index", inplace=True)
            marginals.sort_index(axis="columns", inplace=True)

            # extract row and column values from indices if required

            if values_reqd is True:
                rowval = tuple(marginals.index)
                colval = tuple(
                    dict(
                        zip(
                            marginals.columns.names,
                            (col,) if isinstance(col, str) else col,
                        )
                    )
                    for col in marginals.columns
                )

            # Obtain counts as newly instantiated NumPy 2-D array

            counts = marginals.to_numpy(dtype="int32", copy=True)

        else:

            # Orphan node so just use node value counts, sorted by value

            marginals_dict = (
                self.sample[node].value_counts().sort_index().to_dict()
            )
            counts = array(
                [[c] for c in marginals_dict.values()], dtype="int32"
            )

            if values_reqd is True:
                rowval = tuple(marginals_dict.keys())

        # Free memory and record timing information

        if node in parents:
            del marginals
        Timing.record(
            "marginals",
            (len(parents[node]) + 1 if node in parents else 1),
            start,
        )

        return (counts, maxcol, rowval, colval)

    def values(self, nodes: Tuple[str, ...]) -> np.ndarray:
        """Return the numeric values for the specified set of nodes.

        Suitable for passing into e.g. linearRegression fitting function.

        Args:
            nodes: Nodes for which data required.

        Returns:
            Numpy array of values, each column for a node.

        Raises:
            TypeError: If bad arg type.
            ValueError: If bad arg value.
        """
        if (
            not isinstance(nodes, tuple)
            or len(nodes) == 0
            or not all([isinstance(n, str) for n in nodes])
        ):
            raise TypeError("Pandas.values() bad arg type")

        numeric = {n for n, t in self.node_types.items() if t != "category"}
        if len(nodes) != len(set(nodes)) or len(set(nodes) - numeric) != 0:
            raise ValueError("Pandas.values() bad arg values")

        values = self.sample[list(nodes)].values

        return np.array(values)  # type: ignore[no-any-return]

    def as_df(self) -> DataFrame:
        """Return the data as a Pandas dataframe.

        Returns data with current sample size and column order.

        Returns:
            Data as Pandas dataframe.
        """
        return self.sample
