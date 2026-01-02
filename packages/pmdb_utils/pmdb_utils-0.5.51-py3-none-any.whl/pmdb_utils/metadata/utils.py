import polars as pl


def polars_type(entry: dict) -> pl.datatypes.DataType:
    t = entry["dtype"].strip().lower()

    if t == "string":
        return pl.String
    if t == "float":
        return pl.Float64
    if t == "int":
        return pl.Int64
    if t == "boolean":
        return pl.Boolean
    if t == "date":
        return pl.Date
    if t == "datetime":
        return pl.Datetime

    if t == "struct":
        if "fields" not in entry or not isinstance(entry["fields"], list):
            raise ValueError("Struct dtype requires a 'fields' list.")
        fields = {f["name"]: polars_type(f) for f in entry["fields"]}
        return pl.Struct(fields)

    if t.startswith("list<") and t.endswith(">"):
        inner = t[5:-1].strip()
        if inner == "struct":
            if "fields" not in entry or not isinstance(entry["fields"], list):
                raise ValueError(
                    "list<struct> dtype requires a 'fields' list on the entry."
                )
            inner_dtype = pl.Struct(
                {f["name"]: polars_type(f) for f in entry["fields"]}
            )
        else:
            inner_dtype = polars_type({"dtype": inner})
        return pl.List(inner_dtype)

    raise NotImplementedError(f"Type {entry['dtype']} not implemented")


def convert_metadata_to_polars_type(meta: dict, table_name) -> dict[str, pl.DataType]:
    dataset = [d for d in meta[0]["datasets"] if d["name"] == table_name]
    cols = dataset[0]["columns"]
    return {c["name"]: polars_type(c) for c in cols}


def enforce_schema(df: pl.DataFrame, expected: dict[str, pl.DataType]) -> pl.DataFrame:
    out = df
    # create any missing columns with the right dtype (all values null)
    missing = [c for c in expected.keys() if c not in out.columns]
    if missing:
        out = out.with_columns(
            *[pl.lit(None, dtype=expected[c]).alias(c) for c in missing]
        )
    # cast existing columns to the expected dtype (also fixes Null->concrete)
    out = out.with_columns(
        *[pl.col(c).cast(dtype, strict=False) for c, dtype in expected.items()]
    )
    return out
