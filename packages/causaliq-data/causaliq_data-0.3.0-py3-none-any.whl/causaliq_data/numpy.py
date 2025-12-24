# Data concrete implementation with data held in NumPy arrays

from gzip import BadGzipFile
from math import prod
from typing import Any, Dict, Optional, Tuple, cast

from causaliq_core.utils import FileFormatError, is_valid_path
from causaliq_core.utils.timing import Timing
from numpy import (
    array,
    bincount,
    empty,
    float64,
    lexsort,
    ndarray,
    nonzero,
)
from numpy import unique as npunique
from numpy import (
    zeros,
)
from numpy.random import default_rng
from pandas import Categorical, DataFrame, factorize, read_csv
from pandas.errors import EmptyDataError

from causaliq_data import Data, DatasetType
from causaliq_data.pandas import Pandas

MAX_CATEGORY = 100  # maximum number of different values in category


class NumPy(Data):
    """Concrete Data subclass which holds data in NumPy arrays.

    Args:
        data (ndarray): Data provided as a 2-D NumPy array.
        dstype (DatasetType): Type of variables in dataset.
        col_values (dict): Column names and their categorical values
            {node: (val1, val2, ...), ....}.

    Attributes:
        data (ndarray): The original data values.
        sample (ndarray): Sample values of size N, rows possibly reordered.
        nodes (tuple): Internal (i.e. original) node names.
        categories: Categories for each categorical node:
            (ndarray['c1', 'c2', ...], ...).
        order (tuple): Order in which nodes should be processed.
        ext_to_orig (dict): Map from external to original names.
        orig_to_ext (dict): Map from original to external names.
        N (int): Current sample size being used by the algorithm.
        node_types (dict): Node types {n1: t1, n2: ....}.
        dstype (DatasetType): Type of dataset (categorical/numeric/mixed).
        node_values (dict): Values and their counts for categorical nodes
            in sample {n1: {v1: c1, v2: ...}, n2 ...}.

    Raises:
        TypeError: If bad arg type.
        ValueError: If bad arg value.
    """

    MAX_BINCOUNT = 1000000

    def __init__(
        self,
        data: ndarray,
        dstype: DatasetType,
        col_values: Dict[str, Optional[Tuple[str, ...]]],
    ) -> None:

        if (
            not isinstance(data, ndarray)
            or len(data.shape) != 2
            or not isinstance(dstype, (DatasetType, str))
            or dstype not in {v for v in DatasetType}
            or not isinstance(col_values, dict)
            or not all([isinstance(k, str) for k in col_values])
            or (
                dstype == "categorical"
                and (
                    not all(
                        [isinstance(t, tuple) for t in col_values.values()]
                    )
                    or not all(
                        [
                            isinstance(s, str)
                            for t in col_values.values()
                            for s in t  # type: ignore[union-attr]
                        ]
                    )
                )
                or (
                    dstype == "continuous"
                    and not all([v is None for v in col_values.values()])
                )
            )
        ):
            raise TypeError("NumPy() bad arg type")

        if (
            data.shape[0] < 2
            or data.shape[1] < 2
            or data.shape[1] != len(col_values)
            or dstype == "categorical"
            and data.dtype != "uint8"
            or dstype == "continuous"
            and data.dtype != "float32"
        ):
            raise ValueError("NumPy bad arg values")

        self.data = data
        self._nodes = tuple(col_values)

        node_type = "category" if dstype == "categorical" else "float32"
        self._node_types = {n: node_type for n in self.nodes}

        self.categories = (
            array([col_values[n] for n in self.nodes], dtype="object")
            if dstype == "categorical"
            else None
        )
        self.order = tuple(i for i in range(len(self.nodes)))
        self.ext_to_orig = {n: n for n in self.nodes}
        self.orig_to_ext = {n: n for n in self.nodes}
        self.dstype = dstype if isinstance(dstype, str) else dstype.value

        # set N, sample and categorical node_values and counts for that N
        self._node_values: Dict[str, Dict[str, int]] = (
            {}
        )  # Initialize empty, will be populated by set_N
        self.set_N(N=data.shape[0])

    @classmethod
    def read(
        cls, filename: str, dstype: DatasetType, N: Optional[int] = None
    ) -> "NumPy":
        """Read a file into a NumPy object.

        Args:
            filename (str): Full path of data file.
            dstype (DatasetType/str): Type of dataset.
            N (int, optional): Number of rows to read.

        Returns:
            NumPy: Data contained in file.

        Raises:
            TypeError: If argument types incorrect.
            ValueError: If illegal values in args or file.
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
                not isinstance(dstype, (DatasetType, str))
                or dstype not in {v for v in DatasetType}
            )
        ):
            raise TypeError("Bad argument types for data.read")
        if N is not None and N < 2:
            raise ValueError("Bad argument values for data.read")

        is_valid_path(filename)

        if dstype == "mixed":
            raise ValueError("Mixed datasets not supported")

        try:

            # Read from file treating as floats/strings according to dstype

            nrows = {} if N is None else {"nrows": N}
            dtype = "float32" if dstype == "continuous" else "category"
            df = read_csv(  # type: ignore[call-overload]
                filename,
                sep=",",
                header=0,
                encoding="utf-8",
                keep_default_na=False,
                na_values="<NA>",
                dtype=dtype,
                **nrows,
            )

            if N is not None and N > len(df):
                raise ValueError("Bad argument values for NumPy.read")

        except (
            UnicodeDecodeError,
            PermissionError,
            EmptyDataError,
            BadGzipFile,
        ) as e:
            raise FileFormatError("File format error: {}".format(e))

        return NumPy.from_df(df, dstype, keep_df=False)

    @classmethod
    def from_df(
        cls, df: DataFrame, dstype: DatasetType, keep_df: bool
    ) -> "NumPy":
        """Create a NumPy object from a Pandas dataframe.

        Used externally just for unit testing.

        Args:
            df (DataFrame): Pandas dataframe containing the data.
            dstype (DatasetType/str): Type of dataset.
            keep_df (bool): Whether df is retained or overwritten -
                the latter is more memory efficient.

        Returns:
            NumPy: Data contained in dataframe.

        Raises:
            TypeError: If argument types incorrect.
            ValueError: If illegal values in args or dataframe.
            FileFormatError: If format issues with dataframe.
        """
        if (
            not isinstance(df, DataFrame)
            or not isinstance(keep_df, bool)
            or (
                not isinstance(dstype, (DatasetType, str))
                or dstype not in {v for v in DatasetType}
            )
        ):
            raise TypeError("NumPy.from_df() bad arg type")

        dtypes = {df[c].dtype.__str__() for c in df.columns}
        if (
            len(df.columns) == 1
            or len(df) == 1
            or (dstype == "categorical" and dtypes != {"category"})
            or (dstype == "continuous" and dtypes != {"float32"})
        ):
            raise ValueError("NumPy.from_df() bad arg value")

        # if keep_df is True:
        #     df = df.copy()
        df2 = df.copy(deep=True) if keep_df is True else df

        if dstype == "categorical":

            # convert categorical values to integer codes, and capture code to
            # value mapping as a tuple for each node, i.e. ('yes', 'no')
            # implies integer code 0 maps to 'yes', 1 to 'no'

            col_values: Dict[str, Optional[Tuple[str, ...]]] = {}
            for col in df2.columns:
                df2[col], uniques = factorize(df2[col])
                if len(uniques) > MAX_CATEGORY:
                    raise ValueError("data.read() too many categories")
                # Handle the case where uniques might be
                # Index or CategoricalIndex
                if hasattr(uniques, "categories") and hasattr(
                    uniques, "codes"
                ):
                    # CategoricalIndex case
                    unique_values = uniques.categories[
                        uniques.codes
                    ].unique()  # type: ignore[attr-defined]
                else:
                    # Regular Index case
                    # type: ignore[attr-defined]
                    unique_values = uniques.unique()
                col_values[col] = tuple(unique_values)
        else:

            # col_values just holds node names for continuous data

            col_values = cast(
                Dict[str, Optional[Tuple[str, ...]]],
                {col: None for col in df.columns},
            )

        # convert data frame to numpy array of appropriate dtype

        dtype = "uint8" if dstype == "categorical" else "float32"
        data = df2.to_numpy(dtype=dtype)

        return NumPy(data, dstype, col_values)

    def set_N(
        self,
        N: int,
        seed: Optional[int] = None,
        random_selection: bool = False,
    ) -> None:
        """Set current working sample size, and optionally randomise
        the row order.

        Args:
            N (int): Current working sample size.
            seed (int, optional): Seed for row order randomisation if required,
                0 and None both imply original order.
            random_selection (bool): Whether rows selected is also randomised.

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
            raise TypeError("NumPy.set_N() bad arg type")

        if (
            N < 1
            or N > self.data.shape[0]
            or (seed is not None and (seed < 0 or seed > 100))
        ):
            raise ValueError("NumPy.set_N() bad arg value")

        self._N = N
        rng = (
            default_rng(seed)
            if seed is not None and seed != 0
            else default_rng(0)
        )

        if random_selection is True:

            # Choose a random selection of rows from data

            indices = rng.choice(self.data.shape[0], size=N, replace=False)
            self._sample = (
                self.data[sorted(indices)]
                if seed is None or seed == 0
                else self.data[indices]
            )

            # Shuffle sample row order if needed (this second shuffle is
            # redundant but is retained to maintain compatability with)

            # if seed is not None and seed != 0:
            #     rng.shuffle(self.sample)  # Shuffle in-place

        else:

            # Always use first N rows of data

            self._sample = self.data[:N, :]

            # Shuffle sample row order if seed is specified

            if seed is not None and seed != 0:
                order = rng.permutation(N)
                self._sample = self.sample[order]

        # compute the node values and counts for categorical variables for
        # the sample

        self._node_values = {}
        if self.dstype == "categorical":
            for j in range(self.sample.shape[1]):
                counts = {
                    self.categories[j][v]: c  # type: ignore[index]
                    for v, c in enumerate(bincount(self.sample[:, j]))
                }
                counts = {v: counts[v] for v in sorted(counts)}
                self._node_values[self.orig_to_ext[self.nodes[j]]] = counts

        # change continuous data to float64 for precision in score calcs. Doing
        # it here means it is only done once for each sample.

        if self.dstype == "continuous":
            sorted_idx = lexsort(self.sample[:, ::-1].T)
            self._sample = self.sample[sorted_idx].astype(float64)

    def _update_sample(
        self,
        old_N: Optional[int] = None,
        old_ext_to_orig: Optional[Dict] = None,
    ) -> None:
        pass

    def randomise_names(self, seed: Optional[int] = None) -> None:
        """Randomises the node names that the learning algorithm uses.

        So sensitivity to these names can be assessed.

        Args:
            seed (int, optional): Randomisation seed. If None, names revert
                back to original names.

        Raises:
            TypeError: For bad argument types.
            ValueError: For bad argument values.
        """
        if seed is not None and not isinstance(seed, int):
            raise TypeError("Data.randomise_names() bad arg type")

        # Generate new column names

        old_orig_to_ext = {orig: ext for orig, ext in self.orig_to_ext.items()}
        self._generate_random_names(seed)

        # Update keys in node_types and node_values

        map = {
            old_orig_to_ext[orig]: self.orig_to_ext[orig]
            for orig in self.orig_to_ext
        }
        self.node_values = {map[n]: vc for n, vc in self.node_values.items()}
        self.node_types = {map[n]: t for n, t in self.node_types.items()}

    def unique(self, j_reqd: tuple, num_vals: ndarray) -> tuple:
        """Counts unique combinations of categorical variables in
        specified set of columns.

        Args:
            j_reqd (tuple): Indices of columns required.
            num_vals (ndarray): Number of values in each of those columns.

        Returns:
            tuple: (ndarray: array of unique combinations,
                    ndarray: vector of corresponding counts).
        """
        minlength = prod(num_vals.tolist())

        if minlength <= self.MAX_BINCOUNT:

            # If maximum number of possible combinations below threshold then
            # pack combinations into integers, and count those for speed.
            # First, generate the packed integers

            multipliers = array(
                [prod((num_vals[:i]).tolist()) for i in range(len(j_reqd))]
            )
            packed = self.sample[:, j_reqd] @ multipliers

            # Count the frquency of unique packed integers, removing all
            # entries with zero counts

            counts = bincount(packed, minlength=minlength)
            packed = nonzero(counts)[0]
            counts = counts[packed]

            # Unpack integers back into their combinations of values using
            # the same multipliers used to pack them into one integer

            combos: ndarray = empty((len(packed), len(multipliers)), dtype=int)
            for jj, r in enumerate(reversed(multipliers)):
                combos[:, len(multipliers) - jj - 1] = packed // r
                packed = packed % r

        else:

            # If maximum number of possible combinations above threshold then
            # using the much slower numpy unique function.

            combos, counts = npunique(
                self.sample[:, j_reqd], axis=0, return_counts=True
            )

        return combos, counts

    def marginals(
        self, node: str, parents: Dict, values_reqd: bool = False
    ) -> tuple:
        """Return marginal counts for a node and its parents.

        Args:
            node (str): Node for which marginals required.
            parents (dict): {node: parents} parents of non-orphan nodes.
            values_reqd (bool): Whether parent and child values required.

        Returns:
            tuple: Of counts, and optionally, values:
                - ndarray counts: 2D, rows=child, cols=parents
                - int maxcol: maximum number of parental values
                - tuple rowval: child values for each row
                - tuple colval: parent combo (dict) for each col

        Raises:
            TypeError: For bad argument types.
            ValueError: For bad argument values.
        """
        if (
            not isinstance(node, str)
            or not isinstance(parents, dict)
            or not all([isinstance(p, list) for p in parents.values()])
            or not isinstance(values_reqd, bool)
        ):
            raise TypeError("NumPy.marginals() bad arg type")

        # determine nodes (external names) for which marginals required

        nodes = tuple([node] + parents[node]) if node in parents else (node,)
        if len(set(nodes) - set(self.node_values)) != 0 or len(nodes) != len(
            set(nodes)
        ):
            raise ValueError("NumPy.marginals() bad arg value")

        maxcol = 1
        rowval = colval = None
        start = Timing.now()

        if len(nodes) == 1:

            # marginals for a single variable - just use node_values

            counts = array(
                [[c] for c in self.node_values[node].values()], dtype=int
            )
            if values_reqd is True:
                rowval = tuple(self.node_values[node].keys())

        else:

            # Determine required column indices and number of unique values
            # in each column.

            j_reqd = tuple(
                self.nodes.index(self.ext_to_orig[n]) for n in nodes
            )
            num_vals = array([len(self.node_values[n]) for n in nodes])
            maxcol = prod((num_vals[1:]).tolist())

            # identify and count unique combinations of node values

            combos, _counts = self.unique(j_reqd, num_vals)

            # separate the child values and parental combinations

            c_values = array(range(len(self.node_values[node])))
            p_combos = npunique(combos[:, 1:], axis=0)

            # initialise and populate the crosstab-style matrix where rows
            # are child values, and columns are unique parental combinations.

            c_value_to_i = {v: i for i, v in enumerate(c_values)}
            p_combo_to_j = {tuple(c): j for j, c in enumerate(p_combos)}
            counts = zeros((len(c_values), len(p_combos)), dtype="int32")
            for idx, (c_value, *p_combo) in enumerate(combos):
                i = c_value_to_i[c_value]
                j = p_combo_to_j[tuple(p_combo)]
                counts[i, j] = _counts[idx]

            # Generate child category corresponding to each row, and parental
            # category combination to each column if required.

            if values_reqd is True:
                rowval = tuple(
                    self.categories[j_reqd[0]]  # type: ignore[index]
                )
                colval = tuple(
                    {
                        self.orig_to_ext[self.nodes[j_reqd[j]]]: (
                            self.categories[j_reqd[j]][  # type: ignore[index]
                                c[j - 1]
                            ]
                        )
                        for j in range(1, len(j_reqd))
                    }
                    for c in p_combos
                )

            c_values = p_combos = c_value_to_i = p_combo_to_j = cast(Any, None)
            _counts = combos = cast(Any, None)

        Timing.record("marginals", len(nodes), start)

        return (counts, maxcol, rowval, colval)

    def values(self, nodes: tuple) -> ndarray:
        """Return the (float) values for the specified set of nodes.

        Suitable for passing into e.g. linearRegression fitting function.

        Args:
            nodes (tuple): Nodes for which data required.

        Returns:
            ndarray: Numpy array of values, each column for a node.

        Raises:
            TypeError: If bad arg type.
            ValueError: If bad arg value.
        """
        if (
            not isinstance(nodes, tuple)
            or len(nodes) == 0
            or not all([isinstance(n, str) for n in nodes])
        ):
            raise TypeError("NumPy.values() bad arg type")

        numeric = {n for n, t in self.node_types.items() if t != "category"}
        if len(nodes) != len(set(nodes)) or len(set(nodes) - numeric) != 0:
            raise ValueError("NumPy.values() bad arg values")

        return self.sample[
            :, [self.nodes.index(self.ext_to_orig[n]) for n in nodes]
        ]

    def as_df(self) -> DataFrame:
        """Return the data as a Pandas dataframe.

        With current sample size, column names and column order.

        Returns:
            DataFrame: Data as Pandas dataframe.
        """

        # convert NumPy array to Pandas DataFrame of appropriate type

        dtype = "uint8" if self.dstype == "categorical" else "float32"
        df = DataFrame(data=self.sample, dtype=dtype, columns=self.nodes)

        # Convert integers representing categories back to categories

        if self.dstype == "categorical":
            for j in range(len(df.columns)):
                # Extract the integer codes first to avoid dtype warnings
                codes = df.iloc[:, j].values
                categorical_data = Categorical.from_codes(
                    codes,  # type: ignore[arg-type]
                    categories=self.categories[j],  # type: ignore[index]
                )
                # Use column assignment instead of iloc to avoid dtype warnings
                df[df.columns[j]] = categorical_data

        # reorder and rename the columns if required

        if (
            self.order != tuple(range(self.data.shape[1]))
            or self.orig_to_ext != self.ext_to_orig
        ):
            order = list(self.orig_to_ext[self.nodes[j]] for j in self.order)
            df = df.rename(columns=self.orig_to_ext).reindex(columns=order)

        return df

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
    def sample(self) -> ndarray:
        """Access to underlying data sample."""
        return self._sample

    @sample.setter
    def sample(self, value: ndarray) -> None:
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
    def node_values(self) -> Dict[str, Dict[str, int]]:
        """Return node values for categorical variables."""
        return self._node_values

    @node_values.setter
    def node_values(self, value: Dict[str, Dict[str, int]]) -> None:
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
            filename (str): Full path of data file.
            compress (bool): Whether to gzip compress the file.
            sf (int): Number of s.f. to retain for numeric values.
            zero (float, optional): Abs values below this counted as zero.
            preserve (bool): Whether self.df is left unchanged by this
                function, False conserves memory if writing out large files.

        Raises:
            TypeError: If argument types incorrect.
            ValueError: If data has no columns defined.
            FileNotFoundError: If destination folder does not exist.
        """
        pandas = Pandas(df=self.as_df())
        pandas.write(filename, compress, sf, zero, preserve)
