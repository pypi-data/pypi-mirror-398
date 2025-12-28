"""Type definitions for WOWSQL SDK."""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union, Tuple
from typing_extensions import NotRequired


class FilterExpression(TypedDict, total=False):
    """Filter expression for queries."""
    column: str
    operator: Literal["eq", "neq", "gt", "gte", "lt", "lte", "like", "is", "in", "not_in", "between", "not_between", "is_not"]
    value: Union[str, int, float, bool, None, List[Any], Tuple[Any, Any]]
    logical_op: NotRequired[Literal["AND", "OR"]]  # For combining filters


class HavingFilter(TypedDict):
    """HAVING clause filter for aggregated results."""
    column: str  # Can be aggregate function like "COUNT(*)" or column name
    operator: Literal["eq", "neq", "gt", "gte", "lt", "lte"]
    value: Union[str, int, float, bool, None]


class OrderByItem(TypedDict):
    """Order by item for multiple column sorting."""
    column: str
    direction: Literal["asc", "desc"]


class QueryOptions(TypedDict, total=False):
    """Options for querying records."""
    select: NotRequired[Union[str, List[str]]]  # Can include expressions like "COUNT(*)", "DATE(created_at) as date"
    filter: NotRequired[Union[FilterExpression, List[FilterExpression]]]
    group_by: NotRequired[Union[str, List[str]]]  # Columns to group by
    having: NotRequired[Union[HavingFilter, List[HavingFilter]]]  # HAVING clause filters
    order: NotRequired[Union[str, List[OrderByItem]]]  # Single column (str) or multiple (List[OrderByItem])
    order_direction: NotRequired[Literal["asc", "desc"]]  # Used only if order is a string
    limit: NotRequired[int]
    offset: NotRequired[int]


class QueryResponse(TypedDict):
    """Response from a query operation."""
    data: List[Dict[str, Any]]
    count: int
    total: int
    limit: int
    offset: int


class CreateResponse(TypedDict):
    """Response from a create operation."""
    id: Union[int, str]
    message: str


class UpdateResponse(TypedDict):
    """Response from an update operation."""
    message: str
    affected_rows: int


class DeleteResponse(TypedDict):
    """Response from a delete operation."""
    message: str
    affected_rows: int


class ColumnInfo(TypedDict):
    """Column information in table schema."""
    name: str
    type: str
    nullable: bool
    key: str
    default: Any
    extra: str


class TableSchema(TypedDict):
    """Table schema information."""
    table: str
    columns: List[ColumnInfo]
    primary_key: Optional[str]

