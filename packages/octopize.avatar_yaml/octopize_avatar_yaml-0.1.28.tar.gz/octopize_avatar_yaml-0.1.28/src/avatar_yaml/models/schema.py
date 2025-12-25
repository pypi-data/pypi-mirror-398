from dataclasses import dataclass
from enum import StrEnum

from avatar_yaml.models.common import Metadata, ModelKind


class ColumnType(StrEnum):
    INT = "int"
    BOOL = "bool"
    CATEGORY = "category"
    NUMERIC = "float"
    DATETIME = "datetime"
    DATETIME_TZ = "datetime_tz"


@dataclass(frozen=True)
class TableDataInfo:
    volume: str | None = None
    file: str | None = None
    auto: bool | None = None


@dataclass(frozen=True)
class ColumnInfo:
    field: str
    type: ColumnType | None = None
    value_type: str | None = None
    identifier: bool | None = None
    primary_key: bool | None = None
    time_series_time: bool | None = None


@dataclass(frozen=True)
class LinkMethod(StrEnum):
    """Available assignment methods to link a child to its parent table after the anonymization."""

    LINEAR_SUM_ASSIGNMENT = "linear_sum_assignment"
    """Assign using the linear sum assignment algorithm.
    This method is a good privacy and utility trade-off. The algorithm consumes lots of resources.
    """
    MINIMUM_DISTANCE_ASSIGNMENT = "minimum_distance_assignment"
    """Assign using the minimum distance assignment algorithm.
    This method assigns the closest child to the parent. It is an acceptable privacy and utility
    trade-off.
    This algorithm consumes less resources than the linear sum assignment."""
    SENSITIVE_ORIGINAL_ORDER_ASSIGNMENT = "sensitive_original_order_assignment"
    """Assign the child to the parent using the original order.
    WARNING!!! This method is a HIGH PRIVACY BREACH as it keeps the original order to assign
    the child to the parent.
    This method isn't recommended for privacy reasons but consumes less resources than the other
    methods."""
    TIME_SERIES = "time_series"
    """Specific assignment method for time series data.
    It is used to link time series data to the parent table."""


@dataclass(frozen=True)
class TableLinkInfoSpec:
    """Destination part of a table link."""

    table: str
    field: str


@dataclass(frozen=True)
class TableLinkInfo:
    """A link from a field to a field in another table."""

    field: str
    to: TableLinkInfoSpec
    method: LinkMethod


@dataclass(frozen=False)
class TableInfo:
    name: str
    data: TableDataInfo | None = None
    individual_level: bool | None = None
    avatars_data: TableDataInfo | None = None
    columns: list[ColumnInfo] | None = None
    links: list[TableLinkInfo] | None = None


@dataclass(frozen=True)
class SchemaSpec:
    tables: list[TableInfo]
    schema_ref: str | None = None


@dataclass(frozen=True)
class Schema:
    kind: ModelKind
    metadata: Metadata
    spec: SchemaSpec


def get_schema(name: str, tables: list[TableInfo], schema_ref: str | None = None) -> Schema:
    return Schema(
        kind=ModelKind.SCHEMA,
        metadata=Metadata(name=name),
        spec=SchemaSpec(
            tables=tables,
            schema_ref=schema_ref,
        ),
    )
