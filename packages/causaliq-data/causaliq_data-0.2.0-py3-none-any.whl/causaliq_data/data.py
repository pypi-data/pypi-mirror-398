"""Abstract data interfaces for causal discovery and BN fitting."""

from abc import abstractmethod
from typing import Any, Dict, Optional, Tuple

import numpy as np
from causaliq_core.bn.bnfit import BNFit
from causaliq_core.utils.random import RandomIntegers
from strenum import StrEnum


class DatasetType(StrEnum):
    CATEGORICAL = "categorical"  # all categorical variables
    CONTINUOUS = "continuous"  # all float variables
    MIXED = "mixed"  # mixed categorical, float or numeric


class VariableType(StrEnum):
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    CATEGORY = "category"


class Data(BNFit):
    """Top level data object that implements BNFit interface.

    Extends BNFit interface with additional methods needed for
    causal structure learning algorithms.

    Attributes:
        elapsed: Elapsed time for operations.
        order: Order in which nodes should be processed.
        ext_to_orig: Map from external to original names.
        orig_to_ext: Map from original to external names.
        dstype: Overall dataset type (categorical/continuous/mixed).

    Properties (from BNFit):
        nodes: Internal (i.e. original) node names.
        N: Current sample size being used by the algorithm.
        node_types: Node types, e.g. {node1: type1, node2: type2}.
        node_values: Values and their counts of categorical nodes.
        sample: Access to underlying data sample.
    """

    elapsed: float = 0.0

    def __init__(self) -> None:
        pass

    def set_order(self, order: Tuple[str, ...]) -> None:
        """Set the process order of the nodes to specified one.

        Args:
            order: New process order.

        Raises:
            TypeError: For bad argument types.
            ValueError: For bad argument values.
        """
        if not isinstance(order, tuple) or any(
            not isinstance(n, str) for n in order
        ):
            raise TypeError("Data.set_order() bad arg type")

        if set(order) != set(self.ext_to_orig.keys()):
            raise ValueError("Data.set_order() bad arg value")

        self.order = tuple(
            self.nodes.index(self.ext_to_orig[n]) for n in order
        )
        if self.__class__.__name__ == "Pandas":
            self._update_sample()

    def get_order(self) -> Tuple[str, ...]:
        """Get the current process order.

        Returns:
            External names of nodes in process order.
        """
        return tuple(self.orig_to_ext[self.nodes[i]] for i in self.order)

    def randomise_order(self, seed: int) -> None:
        """Randomise the process order of the nodes.

        Args:
            seed: Randomisation seed.

        Raises:
            TypeError: For bad argument types.
            ValueError: For bad argument values.
        """
        if not isinstance(seed, int):
            raise TypeError("Data.randomise_order() bad arg type")

        if seed < 0:
            raise ValueError("Data.randomise_order() bad arg value")

        self.order = tuple(RandomIntegers(len(self.nodes), seed))
        if self.__class__.__name__ == "Pandas":
            self._update_sample()

    def _set_dstype(self) -> None:
        """Determine overall dataset type from individual node types."""
        n_floats = sum(
            1 if v in {"float32", "float64"} else 0
            for v in self.node_types.values()
        )
        n_cats = sum(
            1 if v == "category" else 0 for v in self.node_types.values()
        )
        self.dstype = (
            "continuous"
            if n_floats == len(self.nodes)
            else ("categorical" if n_cats == len(self.nodes) else "mixed")
        )

    def _generate_random_names(self, seed: Optional[int]) -> None:
        """Generate randomised external names for nodes."""
        if seed is None:
            self.ext_to_orig = {n: n for n in self.nodes}
            self.orig_to_ext = {n: n for n in self.nodes}
        else:
            ints = [i for i in RandomIntegers(len(self.nodes), seed)]
            self.ext_to_orig = {
                "X{:03d}{}".format(ints[i], n[:6]): n
                for i, n in enumerate(self.nodes)
            }
            self.orig_to_ext = {
                orig: ext for ext, orig in self.ext_to_orig.items()
            }

    @abstractmethod
    def set_N(
        self,
        N: int,
        seed: Optional[int] = None,
        random_selection: bool = False,
    ) -> None:
        """Set current working sample size.

        Args:
            N: Current working sample size.
            seed: Seed for row order randomisation if required.
            random_selection: Whether row selection is also randomised.

        Raises:
            TypeError: If bad argument type.
            ValueError: If bad argument value.
        """
        pass

    @abstractmethod
    def randomise_names(self, seed: Optional[int]) -> None:
        """Randomise the node names that the learning algorithm uses.

        Allows sensitivity to node names to be assessed.

        Args:
            seed: Randomisation seed. If None, names revert back to
                original names.

        Raises:
            TypeError: For bad argument types.
            ValueError: For bad argument values.
        """
        pass

    @abstractmethod
    def _update_sample(
        self,
        old_N: Optional[int] = None,
        old_ext_to_orig: Optional[Dict] = None,
    ) -> None:
        """Update the sample after changes to N or node ordering.

        Args:
            old_N: Previous sample size.
            old_ext_to_orig: Previous external to original name mapping.
        """
        pass

    @abstractmethod
    def marginals(
        self, node: str, parents: Dict, values_reqd: bool = False
    ) -> Tuple:
        """Return marginal counts for a node and its parents.

        Args:
            node: Node for which marginals required.
            parents: Dictionary {node: parents} for non-orphan nodes.
            values_reqd: Whether parent and child values required.

        Returns:
            Tuple of counts, and optionally, values:

            - ndarray counts: 2D array, rows=child, cols=parents
            - int maxcol: Maximum number of parental values
            - tuple rowval: Child values for each row
            - tuple colval: Parent combo (dict) for each col

        Raises:
            TypeError: For bad argument types.
        """
        pass

    @abstractmethod
    def values(self, nodes: Tuple[str, ...]) -> np.ndarray:
        """Return the (float) values for specified nodes.

        Suitable for passing into e.g. linear regression fitting.

        Args:
            nodes: Nodes for which data required.

        Returns:
            Numpy array of values, each column for a node.

        Raises:
            TypeError: If bad argument type.
            ValueError: If bad argument value.
        """
        pass

    @abstractmethod
    def as_df(self) -> Any:
        """Return the data as a Pandas dataframe.

        Returns data with current sample size and column order.

        Returns:
            Data as Pandas DataFrame.
        """
        pass

    # BNFit interface properties

    @property
    @abstractmethod
    def nodes(self) -> Tuple[str, ...]:
        """Column names in the dataset.

        Returns:
            Tuple of node names (column names) in the dataset.
        """
        pass

    @nodes.setter
    @abstractmethod
    def nodes(self, value: Tuple[str, ...]) -> None:
        """Set column names."""
        pass

    @property
    @abstractmethod
    def sample(self) -> Any:
        """Access to underlying data sample.

        Returns:
            The underlying DataFrame or data structure for direct access.
            Used for operations like .unique() on columns.
        """
        pass

    @sample.setter
    @abstractmethod
    def sample(self, value: Any) -> None:
        """Set the underlying data sample."""
        pass

    @property
    @abstractmethod
    def node_types(self) -> Dict[str, str]:
        """Node type mapping for each variable.

        Returns:
            Dictionary mapping node names to their types.
            Format: {node: 'category' | 'continuous'}
        """
        pass

    @node_types.setter
    @abstractmethod
    def node_types(self, value: Dict[str, str]) -> None:
        """Set node type mapping."""
        pass

    @property
    @abstractmethod
    def N(self) -> int:
        """Total sample size.

        Returns:
            Current sample size being used.
        """
        pass

    @N.setter
    @abstractmethod
    def N(self, value: int) -> None:
        """Set total sample size."""
        pass

    @property
    @abstractmethod
    def node_values(self) -> Dict[str, Dict]:
        """Node value counts for categorical variables.

        Returns:
            Values and their counts of categorical nodes in sample.
            Format: {node1: {val1: count1, val2: count2, ...}, ...}
        """
        pass

    @node_values.setter
    @abstractmethod
    def node_values(self, value: Dict[str, Dict]) -> None:
        """Set node value counts."""
        pass

    @abstractmethod
    def write(self, filename: str) -> None:
        """Write data to file.

        Args:
            filename: Path to output file.

        Raises:
            TypeError: If filename is not a string.
            FileNotFoundError: If output directory doesn't exist.
        """
        pass
