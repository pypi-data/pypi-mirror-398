# We'll implement the updated MetaDataGenerator class with nested Struct and typed List support,
# then test it against a Polars schema modeled after the user's Strava example.

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

import polars as pl


@dataclass
class MetaDataGenerator:
    """Generate dataset-scoped metadata JSON from a Polars schema, including nested Struct fields and typed Lists.

    - load_type is placed at the dataset level.
    - Struct columns emit a `"fields"` array with nested field definitions.
    - List columns emit `"dtype": "list<inner>"` where inner is mapped via the same dtype mapping.
    """

    source_name: str
    dataset_name: str
    file_type: str = "parquet"
    load_type: str = "T2Full"
    primary_keys: List[str] = field(default_factory=list)
    exclude_from_diff_compare: List[str] = field(default_factory=list)
    schema: Optional[Union[Dict[str, pl.DataType], "pl.Schema"]] = None
    include_extra_fields: bool = True

    def _base_dtype_to_str(self, dtype: pl.DataType) -> str:
        # Scalar/base types (non-nested). Nested handled separately.
        if dtype in (pl.String, pl.Utf8):
            return "string"
        if dtype in (
            pl.Int8,
            pl.Int16,
            pl.Int32,
            pl.Int64,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
        ):
            return "int"
        if dtype in (pl.Float32, pl.Float64):
            return "float"
        if dtype == pl.Boolean:
            return "boolean"
        # Datetime (any unit/tz)
        if isinstance(dtype, pl.datatypes.Datetime) or dtype == pl.Datetime:
            return "datetime"
        if dtype == pl.Null:
            # Avoid null-only issues; treat as string
            return "string"
        return str(dtype).lower()

    def _field_spec(self, name: str, dtype: pl.DataType) -> Dict:
        """Create a field spec for a Struct's nested fields (recursive)."""
        # Struct inside struct
        if isinstance(dtype, pl.datatypes.Struct) or dtype == pl.Struct:
            fields = []
            # dtype.fields returns list[pl.Field]
            for f in dtype.fields:
                fields.append(self._field_spec(f.name, f.dtype))
            return {"name": name, "dtype": "struct", "fields": fields}

        # List inside struct
        if isinstance(dtype, pl.datatypes.List) or dtype == pl.List:
            inner = dtype.inner
            inner_str = self._dtype_to_str_for_list_inner(inner)
            return {"name": name, "dtype": f"list<{inner_str}>"}

        # Base/other
        return {"name": name, "dtype": self._base_dtype_to_str(dtype)}

    def _dtype_to_str_for_list_inner(self, inner: pl.DataType) -> str:
        # When a list holds structs, we mark as struct (caller won't add fields for list elements by design).
        if isinstance(inner, pl.datatypes.Struct) or inner == pl.Struct:
            return "struct"
        if isinstance(inner, pl.datatypes.List) or inner == pl.List:
            # Nested list-of-list; show as list<...>
            return f"list<{self._dtype_to_str_for_list_inner(inner.inner)}>"
        return self._base_dtype_to_str(inner)

    def _column_spec(self, name: str, dtype: pl.DataType) -> Dict:
        spec = {"name": name}

        # Struct column
        if isinstance(dtype, pl.datatypes.Struct) or dtype == pl.Struct:
            spec["dtype"] = "struct"
            # Build nested fields
            nested_fields = []
            for f in dtype.fields:
                nested_fields.append(self._field_spec(f.name, f.dtype))
            spec["fields"] = nested_fields
            return spec

        # List column
        if isinstance(dtype, pl.datatypes.List) or dtype == pl.List:
            inner = dtype.inner
            inner_str = self._dtype_to_str_for_list_inner(inner)
            spec["dtype"] = f"list<{inner_str}>"
            return spec

        # Base types
        spec["dtype"] = self._base_dtype_to_str(dtype)
        return spec

    def _as_mapping(
        self, schema: Union[Dict[str, pl.DataType], "pl.Schema"]
    ) -> Dict[str, pl.DataType]:
        if isinstance(schema, dict):
            return schema
        if hasattr(schema, "items"):
            return dict(schema.items())
        raise TypeError("schema must be a dict[str, pl.DataType] or pl.Schema")

    def generate(self) -> list[dict]:
        schema_map = self._as_mapping(self.schema)
        exclude = set(self.exclude_from_diff_compare)

        columns = [self._column_spec(name, dtype) for name, dtype in schema_map.items()]

        track_columns = [
            name
            for name in schema_map.keys()
            if name not in exclude and name not in set(self.primary_keys)
        ]

        return [
            {
                "source_name": self.source_name,
                "file_type": self.file_type,
                "datasets": [
                    {
                        "name": self.dataset_name,
                        "load_type": self.load_type,
                        "primary_keys": self.primary_keys,
                        "track_columns": track_columns,
                        "columns": columns,
                    }
                ],
            }
        ]

    def to_json(
        self,
        schema: Union[Dict[str, pl.DataType], "pl.Schema"],
        *,
        indent: Optional[int] = 2,
    ) -> str:
        return json.dumps(self.build(schema), indent=indent)

    def save(
        self,
        schema: Union[Dict[str, pl.DataType], "pl.Schema"],
        path: str,
        *,
        indent: Optional[int] = 2,
    ) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.build(schema), f, indent=indent)
