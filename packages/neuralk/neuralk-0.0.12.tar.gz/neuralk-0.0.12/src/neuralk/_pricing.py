from math import ceil

import polars as pl

_VARIABLE_COST = 1  # Per 1k rows

def compute_credits_to_use_nicl(
    df_predict: pl.DataFrame,
    variable_cost: float = _VARIABLE_COST,
) -> float:
    """
    Estimate the number of credits required for using NICL, which is proportional to the number of rows in the predict.
    If the number of rows is not a multiple of 1000, we round up to the next multiple of 1000.
    (e.g. 1001 rows will cost the same as 2000 rows)

    Parameters
    ----------
    df_predict : pl.DataFrame
        The dataframe to predict on.
    variable_cost : float, default=_VARIABLE_COST
        Cost per additional row beyond the low regime threshold.

    Returns
    -------
    float
        Estimated number of credits for predictions.
    """

    
    return ceil(df_predict.shape[0] / 1000) * variable_cost