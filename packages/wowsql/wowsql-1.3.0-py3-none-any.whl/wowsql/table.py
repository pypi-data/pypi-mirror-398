"""Table and QueryBuilder classes."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, Tuple
from .types import (
    QueryOptions,
    FilterExpression,
    HavingFilter,
    OrderByItem,
    QueryResponse,
    CreateResponse,
    UpdateResponse,
    DeleteResponse,
)

if TYPE_CHECKING:
    from .client import WowSQLClient


class QueryBuilder:
    """Fluent query builder for constructing database queries."""
    
    def __init__(self, client: "WowSQLClient", table_name: str):
        self.client = client
        self.table_name = table_name
        self.options: QueryOptions = {}
    
    def select(self, *columns: Union[str, List[str]]) -> "QueryBuilder":
        """
        Select specific columns or expressions.
        
        Args:
            *columns: Column name(s) or expressions to select (e.g., "COUNT(*)", "DATE(created_at) as date")
            
        Returns:
            Self for chaining
            
        Examples:
            >>> query.select("id", "name")
            >>> query.select("category", "COUNT(*) as count", "AVG(price) as avg_price")
        """
        if len(columns) == 1 and isinstance(columns[0], list):
            self.options["select"] = columns[0]
        else:
            self.options["select"] = list(columns) if len(columns) > 1 else columns[0] if columns else "*"
        return self
    
    def filter(
        self,
        column: Union[str, FilterExpression, Dict[str, Any]],
        operator: Optional[str] = None,
        value: Any = None,
        logical_op: str = "AND"
    ) -> "QueryBuilder":
        """
        Add a filter condition.
        
        Supports multiple calling styles for backward compatibility:
        1. New style: filter(column, operator, value) - e.g., filter("age", "gt", 18)
        2. Dict style: filter({"column": "age", "operator": "gt", "value": 18})
        3. Old style: filter({"age": 18}) - defaults to "eq" operator
        
        Args:
            column: Column name, or FilterExpression dict, or dict with column as key
            operator: Operator (eq, neq, gt, gte, lt, lte, like, in, not_in, between, not_between, is, is_not)
            value: Filter value (for 'in' and 'not_in', use a list; for 'between', use a tuple/list of 2 values)
            logical_op: Logical operator for combining with previous filters ("AND" or "OR")
            
        Returns:
            Self for chaining
            
        Examples:
            >>> query.filter("age", "gt", 18)  # New style
            >>> query.filter({"column": "age", "operator": "gt", "value": 18})  # Dict style
            >>> query.filter({"username": "admin"})  # Old style (defaults to eq)
            >>> query.filter("category", "in", ["electronics", "books"])
        """
        if "filter" not in self.options:
            self.options["filter"] = []
        
        # Handle dict-style filter (backward compatibility)
        if isinstance(column, dict):
            # Check if it's a FilterExpression dict
            if "column" in column and "operator" in column:
                filter_expr: FilterExpression = {
                    "column": column["column"],
                    "operator": column["operator"],
                    "value": column.get("value"),
                    "logical_op": column.get("logical_op", logical_op)
                }
            else:
                # Old style: {"column_name": value} - defaults to "eq" operator
                # Support both single key-value and multiple
                if len(column) == 1:
                    col_name, col_value = next(iter(column.items()))
                    filter_expr: FilterExpression = {
                        "column": col_name,
                        "operator": "eq",
                        "value": col_value,
                        "logical_op": logical_op
                    }
                else:
                    # Multiple filters - convert to list
                    filter_list = []
                    for col_name, col_value in column.items():
                        filter_list.append({
                            "column": col_name,
                            "operator": "eq",
                            "value": col_value,
                            "logical_op": logical_op
                        })
                    current_filter = self.options["filter"]
                    if isinstance(current_filter, list):
                        current_filter.extend(filter_list)
                    else:
                        self.options["filter"] = [current_filter] + filter_list if current_filter else filter_list
                    return self
        else:
            # New style: filter(column, operator, value)
            if operator is None or value is None:
                raise TypeError(
                    f"filter() missing required arguments: 'operator' and 'value'. "
                    f"Use filter(column, operator, value) or filter({{'column': col, 'operator': op, 'value': val}})"
                )
        filter_expr: FilterExpression = {
            "column": column,
            "operator": operator,
            "value": value,
            "logical_op": logical_op
        }
        
        current_filter = self.options["filter"]
        if isinstance(current_filter, list):
            current_filter.append(filter_expr)
        else:
            self.options["filter"] = [current_filter, filter_expr]
        
        return self
    
    # Convenience methods for common operators
    def eq(self, column: str, value: Any) -> "QueryBuilder":
        """Filter where column equals value."""
        return self.filter(column, "eq", value)
    
    def neq(self, column: str, value: Any) -> "QueryBuilder":
        """Filter where column does not equal value."""
        return self.filter(column, "neq", value)
    
    def gt(self, column: str, value: Any) -> "QueryBuilder":
        """Filter where column is greater than value."""
        return self.filter(column, "gt", value)
    
    def gte(self, column: str, value: Any) -> "QueryBuilder":
        """Filter where column is greater than or equal to value."""
        return self.filter(column, "gte", value)
    
    def lt(self, column: str, value: Any) -> "QueryBuilder":
        """Filter where column is less than value."""
        return self.filter(column, "lt", value)
    
    def lte(self, column: str, value: Any) -> "QueryBuilder":
        """Filter where column is less than or equal to value."""
        return self.filter(column, "lte", value)
    
    def like(self, column: str, value: str) -> "QueryBuilder":
        """Filter where column matches pattern (SQL LIKE)."""
        return self.filter(column, "like", value)
    
    def is_null(self, column: str) -> "QueryBuilder":
        """Filter where column IS NULL."""
        return self.filter(column, "is", None)
    
    def is_not_null(self, column: str) -> "QueryBuilder":
        """Filter where column IS NOT NULL."""
        return self.filter(column, "is_not", None)
    
    def in_(self, column: str, values: List[Any]) -> "QueryBuilder":
        """Filter where column is in list of values."""
        return self.filter(column, "in", values)
    
    def not_in(self, column: str, values: List[Any]) -> "QueryBuilder":
        """Filter where column is not in list of values."""
        return self.filter(column, "not_in", values)
    
    def between(self, column: str, min_value: Any, max_value: Any) -> "QueryBuilder":
        """Filter where column is between min and max values."""
        return self.filter(column, "between", [min_value, max_value])
    
    def not_between(self, column: str, min_value: Any, max_value: Any) -> "QueryBuilder":
        """Filter where column is not between min and max values."""
        return self.filter(column, "not_between", [min_value, max_value])
    
    def or_(self, column: str, operator: str, value: Any) -> "QueryBuilder":
        """Add an OR filter condition."""
        return self.filter(column, operator, value, logical_op="OR")
    
    def __getattr__(self, name: str):
        """
        Support Python keywords as method names (workaround for 'or' and 'in').
        
        This allows using .or() and .in() even though they are Python keywords.
        """
        if name == "or":
            return self.or_
        elif name == "in":
            return self.in_
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def execute(self) -> QueryResponse:
        """Execute the query (alias for get)."""
        return self.get()
    
    def order_by(
        self,
        column: Union[str, List[OrderByItem], List[Tuple[str, str]]],
        direction: Optional[str] = None
    ) -> "QueryBuilder":
        """
        Order results by column(s).
        
        Args:
            column: Column name, or list of OrderByItem dicts, or list of (column, direction) tuples
            direction: Sort direction ('asc' or 'desc') - only used if column is a string
            
        Returns:
            Self for chaining
            
        Examples:
            >>> query.order_by("created_at", "desc")
            >>> query.order_by([{"column": "category", "direction": "asc"}, {"column": "price", "direction": "desc"}])
            >>> query.order_by([("created_at", "desc"), ("id", "asc")])
        """
        if isinstance(column, str):
            self.options["order"] = column
            if direction:
                self.options["order_direction"] = direction
        else:
            # Multiple columns
            order_items = []
            for item in column:
                if isinstance(item, dict):
                    order_items.append(item)
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    order_items.append({"column": item[0], "direction": item[1]})
            self.options["order"] = order_items
        return self
    
    def order(self, column: str, direction: str = "asc") -> "QueryBuilder":
        """
        Order results by a single column (alias for order_by for backward compatibility).
        
        Args:
            column: Column to order by
            direction: Sort direction ('asc' or 'desc')
            
        Returns:
            Self for chaining
        """
        return self.order_by(column, direction)
    
    def limit(self, limit: int) -> "QueryBuilder":
        """
        Limit number of results.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            Self for chaining
        """
        self.options["limit"] = limit
        return self
    
    def offset(self, offset: int) -> "QueryBuilder":
        """
        Skip records (pagination).
        
        Args:
            offset: Number of records to skip
            
        Returns:
            Self for chaining
        """
        self.options["offset"] = offset
        return self
    
    def group_by(self, columns: Union[str, List[str]]) -> "QueryBuilder":
        """
        Group results by column(s).
        
        Args:
            columns: Column name(s) or expressions to group by
            
        Returns:
            Self for chaining
            
        Examples:
            >>> query.group_by("category")
            >>> query.group_by(["category", "status"])
            >>> query.group_by("DATE(created_at)")
        """
        if isinstance(columns, str):
            self.options["group_by"] = [columns]
        else:
            self.options["group_by"] = columns
        return self
    
    def having(
        self,
        column: str,
        operator: str,
        value: Any
    ) -> "QueryBuilder":
        """
        Add a HAVING clause filter (for filtering aggregated results).
        
        Args:
            column: Column name or aggregate function (e.g., "COUNT(*)", "SUM(price)")
            operator: Operator (eq, neq, gt, gte, lt, lte)
            value: Filter value
            
        Returns:
            Self for chaining
            
        Examples:
            >>> query.having("COUNT(*)", "gt", 10)
            >>> query.having("AVG(price)", "gte", 50)
        """
        if "having" not in self.options:
            self.options["having"] = []
        
        having_expr: HavingFilter = {
            "column": column,
            "operator": operator,
            "value": value
        }
        
        current_having = self.options["having"]
        if isinstance(current_having, list):
            current_having.append(having_expr)
        else:
            self.options["having"] = [current_having, having_expr]
        
        return self
    
    def get(self, additional_options: Optional[QueryOptions] = None) -> QueryResponse:
        """
        Execute the query using POST /{table}/query endpoint for advanced features.
        
        Args:
            additional_options: Additional query options
            
        Returns:
            Query response with data and metadata
        """
        final_options = {**self.options}
        if additional_options:
            final_options.update(additional_options)
        
        # Build query request body for POST endpoint
        body: Dict[str, Any] = {}
        
        # Select
        if "select" in final_options:
            select_val = final_options["select"]
            if isinstance(select_val, str):
                body["select"] = [s.strip() for s in select_val.split(",")]
            else:
                body["select"] = select_val if isinstance(select_val, list) else [select_val]
        
        # Filters
        if "filter" in final_options:
            filters = final_options["filter"]
            if isinstance(filters, list):
                body["filters"] = filters
            else:
                body["filters"] = [filters]
        
        # Group by
        if "group_by" in final_options:
            group_by_val = final_options["group_by"]
            if isinstance(group_by_val, str):
                body["group_by"] = [s.strip() for s in group_by_val.split(",")]
            else:
                body["group_by"] = group_by_val if isinstance(group_by_val, list) else [group_by_val]
        
        # Having
        if "having" in final_options:
            having_val = final_options["having"]
            if isinstance(having_val, list):
                body["having"] = having_val
            else:
                body["having"] = [having_val]
        
        # Order by
        if "order" in final_options:
            order_val = final_options["order"]
            if isinstance(order_val, str):
                body["order_by"] = order_val
                body["order_direction"] = final_options.get("order_direction", "asc")
            else:
                body["order_by"] = order_val
        
        # Limit and offset
        if "limit" in final_options:
            body["limit"] = final_options["limit"]
        if "offset" in final_options:
            body["offset"] = final_options["offset"]
        
        # Use POST endpoint for advanced queries, GET for simple ones
        has_advanced_features = (
            "group_by" in body or
            "having" in body or
            (isinstance(body.get("order_by"), list)) or
            any(f.get("operator") in ["in", "not_in", "between", "not_between"] for f in body.get("filters", []))
        )
        
        if has_advanced_features:
            return self.client._request("POST", f"/{self.table_name}/query", json=body)
        else:
            # Fallback to GET for simple queries (backward compatibility)
            params = {}
            if "select" in body:
                params["select"] = ",".join(body["select"]) if isinstance(body["select"], list) else body["select"]
            if "filters" in body:
                filter_strs = []
                for f in body["filters"]:
                    if isinstance(f.get("value"), list):
                        # Can't use GET for IN/BETWEEN, must use POST
                        return self.client._request("POST", f"/{self.table_name}/query", json=body)
                    filter_strs.append(f"{f['column']}.{f['operator']}.{f['value']}")
                params["filter"] = ",".join(filter_strs)
            if "order_by" in body and isinstance(body["order_by"], str):
                params["order"] = body["order_by"]
                params["order_direction"] = body.get("order_direction", "asc")
            if "limit" in body:
                params["limit"] = body["limit"]
            if "offset" in body:
                params["offset"] = body["offset"]
            return self.client._request("GET", f"/{self.table_name}", params=params)
    
    def first(self) -> Optional[Dict[str, Any]]:
        """
        Get first record matching query.
        
        Returns:
            First record or None
        """
        result = self.limit(1).get()
        return result["data"][0] if result["data"] else None


class Table:
    """Table interface for database operations."""
    
    def __init__(self, client: "WowSQLClient", table_name: str):
        self.client = client
        self.table_name = table_name
    
    def select(self, columns: Union[str, List[str]]) -> QueryBuilder:
        """
        Start a query with column selection.
        
        Args:
            columns: Column(s) to select
            
        Returns:
            QueryBuilder for chaining
        """
        return QueryBuilder(self.client, self.table_name).select(columns)
    
    def filter(
        self, 
        filter_expr: Union[FilterExpression, Dict[str, Any], str],
        operator: Optional[str] = None,
        value: Any = None,
        logical_op: str = "AND"
    ) -> QueryBuilder:
        """
        Start a query with a filter.
        
        Supports multiple calling styles for backward compatibility:
        1. New style: filter(column, operator, value)
        2. Dict style: filter({"column": "age", "operator": "gt", "value": 18})
        3. Old style: filter({"age": 18}) - defaults to "eq" operator
        
        Args:
            filter_expr: Filter expression dict, or column name (if using new style)
            operator: Operator (if using new style)
            value: Filter value (if using new style)
            logical_op: Logical operator for combining filters
            
        Returns:
            QueryBuilder for chaining
        """
        return QueryBuilder(self.client, self.table_name).filter(filter_expr, operator, value, logical_op)
    
    def get(self, options: Optional[QueryOptions] = None) -> QueryResponse:
        """
        Get all records with optional filters.
        
        Args:
            options: Query options
            
        Returns:
            Query response
        """
        return QueryBuilder(self.client, self.table_name).get(options)
    
    def get_by_id(self, record_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a single record by ID.
        
        Args:
            record_id: Record ID
            
        Returns:
            Record data
        """
        return self.client._request("GET", f"/{self.table_name}/{record_id}")
    
    def create(self, data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new record.
        
        Args:
            data: Record data
            
        Returns:
            Create response with new record ID
        """
        return self.client._request("POST", f"/{self.table_name}", json=data)
    
    def insert(self, data: Dict[str, Any]) -> CreateResponse:
        """
        Insert a new record (alias for create).
        
        Args:
            data: Record data
            
        Returns:
            Create response with new record ID
        """
        return self.create(data)
    
    def update(self, record_id: Union[int, str], data: Dict[str, Any]) -> UpdateResponse:
        """
        Update a record by ID.
        
        Args:
            record_id: Record ID
            data: Data to update
            
        Returns:
            Update response
        """
        return self.client._request("PATCH", f"/{self.table_name}/{record_id}", json=data)
    
    def delete(self, record_id: Union[int, str]) -> DeleteResponse:
        """
        Delete a record by ID.
        
        Args:
            record_id: Record ID
            
        Returns:
            Delete response
        """
        return self.client._request("DELETE", f"/{self.table_name}/{record_id}")

