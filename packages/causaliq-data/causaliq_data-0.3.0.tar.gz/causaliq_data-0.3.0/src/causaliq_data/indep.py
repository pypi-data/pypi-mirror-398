#
#   Functions providing probabilistic independence tests
#

from typing import Any, Dict, List, Optional, Tuple, Union

from causaliq_core.bn import BN
from numpy import log
from pandas import DataFrame, crosstab
from scipy import stats  # type: ignore

from causaliq_data.pandas import Pandas

TESTS = ["mi", "x2"]
TEST_PARAMS = {"alpha": 0.05}

MIN_P_VALUE = 1e-30  # p-values below this are considered to be zero


def check_test_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Checks independence test parameters and sets defaults.

    Args:
        params (dict): Test parameters to check, supports:
            - alpha: float test p-value threshold

    Returns:
        dict: Of test params and values including defaults.

    Raises:
        TypeError: If test_params have wrong type.
        ValueError: If test_params have wrong values.
    """
    params = params.copy()
    defaults = {p: v for p, v in TEST_PARAMS.items() if p not in params}
    params.update(defaults)

    if not isinstance(params["alpha"], float):
        raise TypeError("test alpha not a float")

    if params["alpha"] < 1e-10 or params["alpha"] > (1 - 1e-10):
        raise ValueError("Invalid value for test alpha")

    return params


def indep(
    x: str,
    y: str,
    z: Union[str, List[str], None],
    data: Union[DataFrame, str, None],
    bn: Optional[BN] = None,
    N: int = 1000000000,
    types: Union[str, List[str]] = "mi",
) -> DataFrame:
    """Checks whether variables x and y are independent.

    Optionally conditionally on z variables, in specified data or using
    BN parameters.

    Args:
        x (str): Name of first variable.
        y (str): Name of second variable.
        z (str/list/None): Name(s) of any conditioning variables.
        data (DataFrame/str/None): Data or file containing data.
        bn (BN/None): Bayesian Network to use parameters from.
        N (int): Sample size to use with BN parameters.
        types (str/list): Type/types of independence test to perform.

    Returns:
        DataFrame: Of independence test results, columns are test names,
            rows are statistic, deg. of freedom, p-value.

    Raises:
        TypeError: If arg types incorrect.
        ValueError: If arg values invalid.
        FileNotFoundError: If data file not found.
    """

    def _accumulate_results(
        actuals: List[List[int]],
        types: List[str],
        results: Dict[str, Dict[str, Union[int, float]]],
    ) -> Dict[str, Dict[str, Union[int, float]]]:
        for type in types:
            df, statistic = _statistic(actuals, type)
            results[type]["df"] += df
            results[type]["statistic"] += statistic
        return results

    # Check and standardise input arguments

    z, data, _, types_list = check_indep_args(x, y, z, data, bn, N, types)

    if data is not None:

        # Generate all required contingency tables in one go -
        # rows are values of x, columns are a multi-series with different
        # conditioning values, then y value

        cols = [data[col] for col in z]
        cols.append(data[y])
        contingency = crosstab(data[x], cols)

        y_values = data[y].unique()  # used to order y values consistently
        missing_y_values: List[int] = [0] * len(
            data[x].unique()
        )  # filler for missing y values
    else:
        assert bn is not None  # For mypy - we know bn is not None here
        contingency = (
            bn.marginal_distribution(x, sorted(z) + [y])
            .apply(lambda x: round(N * x))
            .astype(int)
        )
        y_values = bn.cnds[y].node_values()
        # Force typing consistency - won't be used in BN case
        missing_y_values = [0] * len(bn.dag.nodes)
    # print(contingency)

    results = {t: {"df": 0, "statistic": 0.0} for t in types_list}
    if len(z):  # conditional independence

        # Generate all combinations of values of conditioning set variables
        # Loop over all these conditioning set value combinations accumulating
        # statistics from the X vs Y contingency table for each combination.

        pvs = contingency.columns.to_frame(index=False).groupby(z).size().index
        for pv in pvs:
            actuals = []
            for y in y_values:
                col = (pv, y) if isinstance(pv, str) else pv + (y,)
                if col in contingency.columns:
                    actuals.append(list(contingency[col].to_dict().values()))
                else:
                    if missing_y_values is not None:
                        actuals.append(missing_y_values)
                    # If missing_y_values is None, skip this y value
                    # (shouldn't happen with BN)
            # print('Actuals (pvs={}): {}'.format(pv, actuals))
            results = _accumulate_results(actuals, types_list, results)

    else:  # unconditional independence
        actuals = [list(contingency.iloc[i]) for i in range(len(contingency))]
        # print('Actuals (no cond set): {}'.format(actuals))
        results = _accumulate_results(actuals, types_list, results)

    # compute the p-value for each statistic

    for type in types_list:
        p_value = 1.0 - stats.chi2.cdf(
            results[type]["statistic"], results[type]["df"]
        )
        results[type]["p_value"] = p_value if p_value > MIN_P_VALUE else 0.0

    # return independence test results as a DataFrame

    return DataFrame.from_dict(results)


def _statistic(actuals: List[List[int]], type: str) -> Tuple[int, float]:
    """Returns variance (from independence) statistic.

    Returns chi-squared or MI for a 2 variable contingency table.

    Args:
        actuals (list): Array of frequency counts of variables as a list
            of lists (i.e. contingency table).
        type (str): Type of variance statistic to generate e.g. x2 or mi.

    Returns:
        tuple: (degrees of freedom, variance statistic).

    Raises:
        TypeError: For any illegal argument types.
    """
    if (
        not isinstance(actuals, list)
        or not isinstance(type, str)
        or any([not isinstance(a, list) for a in actuals])
    ):
        raise TypeError("_indep_tests bad arg types")

    x_cardinality = len(actuals)
    y_cardinality = len(actuals[0])
    if any([len(a) != y_cardinality for a in actuals]):
        raise TypeError("_indep_tests misshapen actuals arg")

    # print('{}x{} actuals table'.format(x_cardinality, y_cardinality))
    N = sum([sum(a) for a in actuals])
    df = (x_cardinality - 1) * (y_cardinality - 1)
    if N == 0:  # no counts at all in table, assume independence
        return (df, 0.0)

    statistic = 0.0
    for i in range(x_cardinality):
        y_marginal = sum(actuals[i])
        for j in range(y_cardinality):
            x_marginal = sum([actuals[i][j] for i in range(x_cardinality)])
            actual = actuals[i][j]
            expected = x_marginal * y_marginal / N
            # print('Actual {}, expected {}'.format(actual, expected))
            if expected == 0.0:
                pass
            elif type == "x2":
                statistic += (
                    (actual - expected) * (actual - expected)
                ) / expected
            elif type == "mi" and actual != 0:
                statistic += 2.0 * actual * log(actual / expected)

    return (df, statistic)


def check_indep_args(
    x: str,
    y: str,
    z: Union[str, List[str], None],
    data: Union[DataFrame, str, None],
    bn: Optional[BN] = None,
    N: int = 0,
    types: Union[str, List[str]] = "mi",
) -> Tuple[List[str], Optional[DataFrame], Optional[str], List[str]]:
    """Check arguments supplied for independence test functions.

    Args:
        x (str): Name of first variable.
        y (str): Name of second variable.
        z (str/list/None): Name(s) of any conditioning variables.
        data (DataFrame/str): Data or file containing data.
        bn (BN/None): Bayesian Network to use parameters from.
        N (int): Sample size to use with BN parameters.
        types (str/list): Type/types of independence test to perform.

    Returns:
        tuple: Of standardised arguments: z as a list, data as a
            DataFrame, data_file as string or None, and types as list.

    Raises:
        TypeError: If arg types incorrect.
        ValueError: If arg values invalid.
        FileNotFoundError: If data file not found.
    """

    # check primary arg types

    z = [] if z is None else ([z] if isinstance(z, str) else z)
    types = [types] if isinstance(types, str) else types
    if (
        not isinstance(x, str)
        or not isinstance(y, str)
        or (
            not (
                isinstance(z, list) and all([isinstance(_z, str) for _z in z])
            )
        )
        or (
            not (
                isinstance(types, list)
                and all([isinstance(t, str) for t in types])
            )
        )
        or (bn is not None and data is not None)
        or (
            bn is None
            and (not isinstance(data, DataFrame) and not isinstance(data, str))
        )
        or (
            data is None
            and (
                not isinstance(bn, BN)
                or not isinstance(N, int)
                or isinstance(N, bool)
            )
        )
    ):
        raise TypeError("bnlearn_indep called with bad arg types")

    # attempt to read in data if data file specified

    data_file_path: Optional[str] = (
        None if isinstance(data, DataFrame) else data
    )
    processed_data: Optional[DataFrame] = None
    if data_file_path:
        processed_data = Pandas.read(data_file_path, dstype="categorical").df
    elif isinstance(data, DataFrame):
        processed_data = data

    # check no duplicate file names across x, y and z

    varlist = [x] + [y] + z
    if len(varlist) != len(set(varlist)):
        raise ValueError("Duplicate variable names")

    # Check all variables in x, y and z are columns in data or BN

    if processed_data is not None:
        if any([v not in processed_data.columns for v in varlist]):
            raise ValueError("Variables not in data")
    else:
        if bn is not None and any([v not in bn.dag.nodes for v in varlist]):
            raise ValueError("Variables not in BN")

    # Check N is positive

    if N < 0:
        raise ValueError("indep() sample size is negative")

    # Check for empty, duplicate or unsupported test names

    if (
        not len(types)
        or len(types) != len(set(types))
        or any([t not in TESTS for t in types])
    ):
        raise ValueError("Empty, duplicated or unsupported tests specified")

    return (z, processed_data, data_file_path, types)
