from typing import Any, Literal

import polars as pl


def merge_rows(
    df1: pl.DataFrame,
    df2: pl.DataFrame,
    cols: list[str] | None,
) -> tuple[pl.DataFrame, list[tuple[dict[str, Any], dict[str, tuple[Any, Any]]]]]:
    """Merge DataFrames on specified ID columns, resolving conflicts.

    Combine the two DataFrames into one DataFrame as follows:
    - If the combination of `cols` values for a row in one DataFrame
      is not present in the other DataFrame, add that row (with all its columns) to the output DataFrame.
    - If the combination of `cols` values for a row in one DataFrame
      is also present in the other DataFrame,
      merge the two rows into one row as follows:
      - If a column is present in only one of the DataFrames,
        take the value from that DataFrame.
      - If a column is present in both DataFrames,
        but the value is null in one DataFrame,
        take the value from the other DataFrame.
      - If a column is present in both DataFrames with non-null values,
        - if the values are identical, take that value.
        - if the values are different,
          take the value from the first DataFrame.

    Note that each DataFrame may have columns not present in the other DataFrame.
    The merged DataFrame will contain all columns from both DataFrames,
    with nulls filled in as needed.

    Parameters
    ----------
    df1
        First DataFrame.
        Must have all `cols` columns.
        Can have extra columns.
    df2
        Second DataFrame.
        Must have all `cols` columns.
        Can have extra columns.
    cols
        List of columns whose combination of values must be unique per row.
        If None, all columns common to both DataFrames are used.

    Returns
    -------
    merged_df
        A single DataFrame containing the merged data.
    conflicts_info
        List of tuples for each conflicting combination found.
        Each tuple contains:
        - A dict representing the conflicting combination of `cols` values.
          Keys are column names, values are the (conflicting) column values.
        - A dict mapping conflicting column names to a tuple of
          (value_in_df1, value_in_df2).

    Notes
    -----
    This function assumes `df1` and `df2` already have at most one row per key
    combination in `cols` (i.e., are already deduplicated). If they are not,
    a full join can produce duplicated outputs.
    """
    # 1. Infer `cols` (join keys) if not provided.
    #    If None -> all columns common to both DataFrames (in df1 order).
    if cols is None:
        df2_cols = set(df2.columns)
        cols = [c for c in df1.columns if c in df2_cols]

    if not cols:
        raise ValueError("cols must not be empty after inference.")


    # 2. Validate presence of key columns.
    missing_1 = [c for c in cols if c not in df1.columns]
    if missing_1:
        raise KeyError(f"df1 is missing key columns: {missing_1}")

    missing_2 = [c for c in cols if c not in df2.columns]
    if missing_2:
        raise KeyError(f"df2 is missing key columns: {missing_2}")


    # 3. Full outer join on key columns.
    #
    #    `coalesce=True` is critical for full joins:
    #    it ensures the output has a single set of key columns with correct
    #    values even for rows that exist only in df2.
    #
    #    Overlapping non-key columns from df2 will be suffixed with "_df2".
    df2_col_suffix = "_df2"
    merged = df1.join(df2, on=cols, how="full", suffix=df2_col_suffix, coalesce=True)


    # 4. For each non-key column present in BOTH inputs:
    #    - compute conflicts: both non-null AND different
    #    - merge value: fill df1 nulls from df2, otherwise keep df1
    #    - record conflicts_info as required by the signature
    key_set = set(cols)
    overlapping_non_key = [c for c in df1.columns if c in df2.columns and c not in key_set]

    conflict_exprs: list[pl.Expr] = []
    merge_exprs: list[pl.Expr] = []
    drop_cols: list[str] = []

    for col in overlapping_non_key:
        col_df2 = f"{col}{df2_col_suffix}"
        if col_df2 not in merged.columns:
            continue

        # Use a non-strict cast for comparisons/filling to reduce dtype mismatch issues.
        left_dtype = df1.schema.get(col)
        right_for_compare = pl.col(col_df2)
        if left_dtype is not None:
            right_for_compare = right_for_compare.cast(left_dtype, strict=False)

        # Conflict means: both non-null and not equal.
        conflict_flag = (
            pl.col(col).is_not_null()
            & pl.col(col_df2).is_not_null()
            & (pl.col(col) != right_for_compare)
        ).alias(f"__conflict__{col}")

        conflict_exprs.append(conflict_flag)

        # Merge rule:
        # - if df1 is null -> take df2 (casted for consistency)
        # - else -> keep df1 (this also enforces "prefer df1 on conflicts")
        merge_exprs.append(
            pl.when(pl.col(col).is_null())
            .then(right_for_compare)
            .otherwise(pl.col(col))
            .alias(col)
        )

        # We'll drop the suffixed df2 column after producing the merged one.
        drop_cols.append(col_df2)

    # Add conflict flags so we can build conflicts_info in one pass.
    if conflict_exprs:
        merged_with_flags = merged.with_columns(conflict_exprs)
    else:
        merged_with_flags = merged

    # Build conflicts_info: one entry per conflicting key-combination.
    conflicts_info: list[tuple[dict[str, Any], dict[str, tuple[Any, Any]]]] = []
    if conflict_exprs:
        any_conflict = pl.any_horizontal([pl.col(f"__conflict__{c}") for c in overlapping_non_key])
        conflict_rows = merged_with_flags.filter(any_conflict)

        # Pull required values to Python; keep it explicit and predictable.
        select_cols = (
            cols
            + overlapping_non_key
            + [f"{c}_df2" for c in overlapping_non_key if f"{c}_df2" in merged_with_flags.columns]
            + [f"__conflict__{c}" for c in overlapping_non_key]
        )
        for row in conflict_rows.select(select_cols).to_dicts():
            key_dict = {k: row[k] for k in cols}
            col_map: dict[str, tuple[Any, Any]] = {}
            for c in overlapping_non_key:
                if row.get(f"__conflict__{c}", False):
                    col_map[c] = (row.get(c), row.get(f"{c}_df2"))
            conflicts_info.append((key_dict, col_map))

    # Apply merge expressions and drop temporary columns.
    if merge_exprs:
        merged = merged_with_flags.with_columns(merge_exprs)
    else:
        merged = merged_with_flags

    # Drop: suffixed df2 overlapping columns and conflict flags.
    to_drop = drop_cols + [f"__conflict__{c}" for c in overlapping_non_key if f"__conflict__{c}" in merged.columns]
    if to_drop:
        merged = merged.drop(to_drop)

    return merged, conflicts_info


def deduplicate_by_cols(
    df: pl.DataFrame,
    cols: list[str] | None = None,
    keep: Literal["first", "last", "any", "none"] = "first",
    maintain_order: bool = True,
) -> tuple[pl.DataFrame, list[tuple[dict[str, Any], pl.DataFrame]]]:
    """Remove duplicate rows based on specified columns.

    Ensure that each row has a unique combination of values in the `cols` columns.
    If duplicates are found, they are removed,
    and information about the duplicates is returned.

    Parameters
    ----------
    df
        DataFrame to deduplicate.
    cols
        List of columns whose combination of values must be unique per row.
        If None, all columns are used, so duplicates are full-row duplicates.
    keep
        Which duplicate row to keep:
        - "first": keep the first occurrence (default)
        - "last": keep the last occurrence
        - "any": keep an arbitrary occurrence
        - "none": remove all duplicates
    maintain_order
        If True, the order of rows in the output DataFrame
        matches the order of their first occurrence in the input DataFrame.

    Returns
    -------
    deuplicated_df
        DataFrame with unique rows based on `cols`.
    duplicates_info
        List of tuples for each duplicate combination found.
        Each tuple contains:
        - A dict representing the duplicate combination of values in `cols`.
          Keys are column names, values are the (duplicated) column values.
        - A DataFrame containing all rows from `df` that share that duplicate combination.

    Raises
    ------
    KeyError
        If any of the specified `cols` are missing from `df`.
    """
    # Determine `cols` if not provided.
    cols = list(df.columns) if cols is None else list(cols)

    # An empty `cols` doesn't make sense: it would mean every row shares the same key.
    if len(cols) == 0:
        raise ValueError("cols must be a non-empty list (or None to use all columns).")

    # Validate that all columns exist.
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"DataFrame is missing columns: {missing}")

    # Find duplicated combinations of values in `cols`.
    # -------------------------------------------------
    # We group by `cols` and compute group sizes. Any group with size > 1 is duplicated.
    # `maintain_order=True` ensures the resulting groups are ordered by the first time
    # each combination appears in `df` (important for deterministic outputs).
    dup_keys = (
        df.group_by(cols, maintain_order=maintain_order)
        .len()
        .filter(pl.col("len") > 1)
        .drop("len")
        .sort(cols)
    )

    # For each duplicated key combination, return:
    # - combo dict (values in `cols`)
    # - a DataFrame of ALL original rows that share that combo
    #
    # We construct the filter predicate carefully so that NULL matches NULL:
    # - for combo value None -> use `is_null()`
    # - otherwise -> equality with a literal
    duplicates_info: list[tuple[dict[str, Any], pl.DataFrame]] = []
    for combo in dup_keys.to_dicts():
        predicate: pl.Expr | None = None
        for c in cols:
            v = combo[c]
            expr = pl.col(c).is_null() if v is None else (pl.col(c) == pl.lit(v))
            predicate = expr if predicate is None else (predicate & expr)

        # cols is non-empty, so predicate must exist.
        assert predicate is not None
        group_df = df.filter(predicate)
        duplicates_info.append((combo, group_df))

    # Remove duplicates, keeping one occurrence
    deduplicated_df = df.unique(subset=cols, keep=keep, maintain_order=maintain_order)

    return deduplicated_df, duplicates_info
