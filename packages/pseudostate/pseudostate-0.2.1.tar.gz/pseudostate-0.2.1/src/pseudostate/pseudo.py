import polars as pl
from polarstate import prepare_event_table, predict_aj_estimates


def calculate_pseudostates(
    times_and_reals: pl.DataFrame,
    fixed_time_horizon: int,
) -> pl.DataFrame:
    """
    Compute Aalen Johansen pseudo-observations at a fixed time horizon.

    This function computes jackknife pseudo-observations for state
    occupation probabilities (or related Aalen Johansen estimands)
    evaluated at a fixed time horizon. Pseudo-observations are constructed
    using a leave-one-out scheme:

        pseudo_i = n * theta_full - (n - 1) * theta_{(-i)}

    where ``theta_full`` is the Aalen Johansen estimate based on the full
    sample, and ``theta_{(-i)}`` is the estimate obtained after removing
    individual ``i``.

    The resulting pseudo-observations can be used as individual-level
    outcomes in regression models (e.g., GEE or GLM) to assess covariate
    effects on cumulative incidence or state occupation probabilities.

    Parameters
    ----------
    times_and_reals : pl.DataFrame
        Input data containing individual event times and realized states.
        Must be compatible with ``prepare_event_table`` and
        ``predict_aj_estimates``. Each row corresponds to a single
        individual.

    fixed_time_horizon : int
        Time point at which the Aalen Johansen estimates are evaluated.

    Returns
    -------
    pl.DataFrame
        A Polars DataFrame containing pseudo-observations for each
        individual. The output includes:

        - Identifier columns (e.g., state, time, horizon) copied from the
          full-sample Aalen Johansen estimate.
        - Numeric columns containing the pseudo-observations.
        - A ``row_id`` column indicating the index of the left-out
          observation.

        For each numeric column, the mean of the pseudo-observations equals
        the corresponding full-sample Aalen Johansen estimate.

    Notes
    -----
    - This implementation uses an explicit leave-one-out loop and therefore
      has time complexity O(n²). It is intended for methodological work,
      simulations, or moderate sample sizes.
    - In the absence of censoring, the pseudo-observations reduce to the
      empirical individual contributions.
    - Non-numeric columns (e.g., state labels) are treated as identifiers
      and are not transformed.

    References
    ----------
    Andersen, P. K., & Pohar Perme, M. (2010).
    Pseudo-observations in survival analysis.
    *Statistical Methods in Medical Research*, 19(1), 71–99.
    """
    n = times_and_reals.height

    full_event_table = prepare_event_table(times_and_reals)
    theta_full = predict_aj_estimates(
        full_event_table,
        fixed_time_horizons=pl.Series([fixed_time_horizon]),
    )

    numeric_cols = [
        c for c, dt in zip(theta_full.columns, theta_full.dtypes) if dt.is_numeric()
    ]
    id_cols = [c for c in theta_full.columns if c not in numeric_cols]

    pseudo_rows: list[pl.DataFrame] = []

    for i in range(n):
        sub_data = times_and_reals.slice(0, i).vstack(times_and_reals.slice(i + 1))

        sub_event_table = prepare_event_table(sub_data)
        theta_loo = predict_aj_estimates(
            sub_event_table,
            fixed_time_horizons=pl.Series([fixed_time_horizon]),
        )

        theta_loo_num = theta_loo.select(numeric_cols)

        pseudo_i = (
            theta_full.select(id_cols + numeric_cols)
            .with_columns(
                [
                    (pl.col(c) * n - pl.lit(n - 1) * theta_loo_num.get_column(c)).alias(
                        c
                    )
                    for c in numeric_cols
                ]
            )
            .with_columns(pl.lit(i).alias("row_id"))
        )

        pseudo_rows.append(pseudo_i)

    return pl.concat(pseudo_rows, how="vertical")
