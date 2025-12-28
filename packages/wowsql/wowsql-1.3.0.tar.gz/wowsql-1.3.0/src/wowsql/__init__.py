"""
WowSQL Python SDK
Official client library for WowSQL REST API v2
"""

from .auth import (
    ProjectAuthClient,
    AuthResponse,
    AuthSession,
    AuthUser,
    TokenStorage,
    MemoryTokenStorage,
)
from .client import WowSQLClient, WowSQLError
from .table import Table, QueryBuilder
from .types import (
    QueryOptions,
    FilterExpression,
    QueryResponse,
    CreateResponse,
    UpdateResponse,
    DeleteResponse,
    TableSchema,
    ColumnInfo,
)
from .storage import (
    WowSQLStorage,
    StorageQuota,
    StorageFile,
    StorageError,
    StorageLimitExceededError,
)
from .schema import (
    WowSQLSchema,
    PermissionError,
)

__version__ = "1.3.0"
__all__ = [
    # Database Client
    "WowSQLClient",
    "WowSQLError",
    "ProjectAuthClient",
    "Table",
    "QueryBuilder",
    # Types
    "QueryOptions",
    "FilterExpression",
    "QueryResponse",
    "CreateResponse",
    "UpdateResponse",
    "DeleteResponse",
    "TableSchema",
    "ColumnInfo",
    # Storage Client
    "WowSQLStorage",
    "StorageQuota",
    "StorageFile",
    "StorageError",
    "StorageLimitExceededError",
    # Schema Management
    "WowSQLSchema",
    "PermissionError",
    # Auth
    "AuthUser",
    "AuthSession",
    "AuthResponse",
    "TokenStorage",
    "MemoryTokenStorage",
]
