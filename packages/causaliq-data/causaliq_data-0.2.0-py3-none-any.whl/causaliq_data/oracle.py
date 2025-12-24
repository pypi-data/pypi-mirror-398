# Concrete subclass of Data which implements an oracle data source

from typing import Any, Dict, Optional, Tuple

import numpy as np
from numpy import float64

from causaliq_data import Data, VariableType


class Oracle(Data):
    def __init__(self, bn: Any) -> None:
        if type(bn).__name__ != "BN":
            raise TypeError("Oracle() bad arg type")

        self.bn = bn
        self._nodes = tuple(bn.dag.nodes)
        self.order = tuple(i for i in range(len(self.nodes)))
        self.ext_to_orig = {n: n for n in self.nodes}
        self.orig_to_ext = {n: n for n in self.nodes}
        self._node_types = {
            n: (
                VariableType.CATEGORY
                if self.bn.cnds[n].__class__.__name__ == "CPT"
                else VariableType.FLOAT32
            )
            for n in self.nodes
        }
        self._set_dstype()
        self._N = 1

    def set_N(
        self,
        N: int,
        seed: Optional[int] = None,
        random_selection: bool = False,
    ) -> None:
        """
        Set current working sample size.

        Args:
            N (int): current working sample size
            seed (int, optional): seed for row order randomisation if reqd.

        Raises:
            TypeError: if bad argument type
            ValueError: if bad argument value
        """
        if not isinstance(N, int) or isinstance(N, bool) or seed is not None:
            raise TypeError("Data.set_N() bad arg type")

        if N < 1:
            raise ValueError("Data.set_N() bad arg value")

        self._N = N

    def marginals(
        self, node: str, parents: Dict, values_reqd: bool = False
    ) -> Tuple:
        """
        Return marginal counts for a node and its parents.

        Args:
            node (str): node for which marginals required.
            parents (dict): {node: parents} parents of non-orphan nodes
            values_reqd (bool): whether parent and child values required

        Raises:
            TypeError: for bad argument types

        Returns:
            tuple: of counts, and optionally, values:
                - ndarray counts: 2D, rows=child, cols=parents
                - int maxcol: maximum number of parental values
                - tuple rowval: child values for each row
                - tuple colval: parent combo (dict) for each col
        """
        if (
            not isinstance(node, str)
            or not isinstance(parents, dict)
            or not all([isinstance(p, list) for p in parents.values()])
            or not isinstance(values_reqd, bool)
        ):
            raise TypeError("Oracle.marginals() bad arg type")

        # obtain marginals as a DataFrame

        nodes = [node] + parents[node] if node in parents else [node]
        marginals = self.bn.marginals(nodes).apply(lambda x: self.N * x)

        # Convert DataFrame to NumPy format

        counts = marginals.to_numpy(dtype=float64, copy=True)
        maxcol = len(marginals.columns)
        rowval = None
        colval = None
        if values_reqd is True:
            rowval = tuple(marginals.index)
            if node in parents:
                colval = tuple(
                    dict(
                        zip(
                            marginals.columns.names,
                            (col,) if isinstance(col, str) else col,
                        )
                    )
                    for col in marginals.columns
                )
        marginals = None

        return (counts, maxcol, rowval, colval)

    def values(self, nodes: Tuple[str, ...]) -> np.ndarray:
        """
        Return the (float) values for the specified set of nodes.

        Args:
            nodes (tuple): nodes for which data required

        Raises:
            TypeError: always raised as not implemented for Oracle
        """
        raise TypeError("Oracle.values() not implemented")

    def _update_sample(
        self,
        old_N: Optional[int] = None,
        old_ext_to_orig: Optional[Dict] = None,
    ) -> None:
        pass

    def randomise_names(self, seed: Optional[int]) -> None:
        """
        Randomises the node names that the learning algorithm uses
        (so sensitivity to these names can be assessed).

        Args:
            seed (int, optional): randomisation seed (if None, names revert
                                  back to original names)

        Raises:
            TypeError: for bad argument types
            ValueError: for bad argument values
        """
        raise NotImplementedError("Data.randomise_names() n/a for Oracle")

    def as_df(self) -> Any:
        """
        Return the data as a Pandas dataframe with current sample size
        and column order.

        Returns:
            DataFrame: data as Pandas
        """
        raise NotImplementedError("Data.df() n/a for Oracle")

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
    def sample(self) -> int:
        """Return the current sample size for Oracle adapter."""
        return self._N

    @sample.setter
    def sample(self, value: int) -> None:
        """Set the current sample size for Oracle adapter."""
        self._N = value

    @property
    def N(self) -> int:
        """Return the current sample size."""
        return self._N

    @N.setter
    def N(self, value: int) -> None:
        """Set the current sample size."""
        self._N = value

    @property
    def node_values(self) -> Dict:
        """Return node values - not applicable for Oracle adapter."""
        return {}

    @node_values.setter
    def node_values(self, value: Dict) -> None:
        """Set node values - not applicable for Oracle adapter."""
        pass

    @property
    def node_types(self) -> Dict:
        """Return the types of all nodes."""
        return self._node_types

    @node_types.setter
    def node_types(self, value: Dict) -> None:
        """Set the node types."""
        self._node_types = value

    def write(self, filename: str) -> None:
        """
        Write data to file - not applicable for Oracle adapter.

        Args:
            filename (str): path to write to

        Raises:
            NotImplementedError: Oracle adapter cannot write data
        """
        raise NotImplementedError("Data.write() n/a for Oracle")
