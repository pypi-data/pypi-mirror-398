def validate_col(df, column_name, allowed_values):
    existing = df[column_name].unique().to_list()
    for item in existing:
        if item not in set(allowed_values):
            raise Exception(f"Unexpected value: {item} [{existing}]")


def rem_validate_col(df, column_name, *args, **kwargs):
    validate_col(df, column_name, *args, **kwargs)
    df = df.drop([column_name])
    return df

def validate_null(df, column_names):
    for item in column_names:
        if df[item].null_count() > 0:
            raise Exception(f"Null value in {item}")

def validate_group_len(df, column_names):
    import polars as pl
    dup_counts = df.group_by(*column_names).len().filter(pl.col("len") > 1).sort("len", descending=True)
    if dup_counts.height > 0:
        raise Exception(f"Duplicates found: {dup_counts}")
