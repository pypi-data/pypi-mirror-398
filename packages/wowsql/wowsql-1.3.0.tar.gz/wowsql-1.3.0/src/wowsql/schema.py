"""
Schema management client for WowSQL.
Requires SERVICE ROLE key.
"""

from typing import List, Dict, Any, Optional
import requests


class PermissionError(Exception):
    """Raised when operation requires service role key but anon key was used"""
    pass


class WowSQLError(Exception):
    """Base exception for WowSQL errors"""
    pass


class WowSQLSchema:
    """
    Schema management client.
    
    ⚠️ IMPORTANT: Requires SERVICE ROLE key, not anonymous key!
    
    Usage:
        schema = WowSQLSchema(
            project_url="https://myproject.wowsql.com",
            service_key="your_service_role_key"  # NOT anon key!
        )
        
        # Create table
        schema.create_table("users", [
            {"name": "id", "type": "INT", "auto_increment": True},
            {"name": "email", "type": "VARCHAR(255)", "unique": True}
        ], primary_key="id")
    """
    
    def __init__(self, project_url: str, service_key: str):
        """
        Initialize schema client.
        
        Args:
            project_url: Project URL (e.g., "https://myproject.wowsql.com")
            service_key: SERVICE ROLE key (not anonymous key!)
        """
        self.base_url = project_url.rstrip("/")
        self.service_key = service_key
        self.headers = {
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json"
        }
    
    def create_table(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
        primary_key: Optional[str] = None,
        indexes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new table.
        
        Args:
            table_name: Name of the table
            columns: List of column definitions
            primary_key: Primary key column name
            indexes: List of columns to index
        
        Example:
            schema.create_table("users", [
                {"name": "id", "type": "INT", "auto_increment": True},
                {"name": "email", "type": "VARCHAR(255)", "unique": True, "nullable": False},
                {"name": "name", "type": "VARCHAR(255)"},
                {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
            ], primary_key="id", indexes=["email"])
        
        Returns:
            Response dict with success status
        
        Raises:
            PermissionError: If using anonymous key instead of service key
            WowSQLError: If table creation fails
        """
        url = f"{self.base_url}/api/v2/schema/tables"
        
        payload = {
            "table_name": table_name,
            "columns": columns,
            "primary_key": primary_key,
            "indexes": indexes
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            
            if response.status_code == 403:
                raise PermissionError(
                    "Schema operations require a SERVICE ROLE key. "
                    "You are using an anonymous key which cannot modify database schema. "
                    "Please use your service role key instead."
                )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise PermissionError(str(e))
            raise WowSQLError(f"Failed to create table: {str(e)}")
    
    def alter_table(
        self,
        table_name: str,
        operation: str,
        column_name: Optional[str] = None,
        column_type: Optional[str] = None,
        new_column_name: Optional[str] = None,
        nullable: bool = True,
        default: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Alter an existing table.
        
        Args:
            table_name: Name of the table
            operation: "add_column", "drop_column", "modify_column", "rename_column"
            column_name: Column name
            column_type: Column type (for add/modify)
            new_column_name: New column name (for rename)
            nullable: Whether column is nullable
            default: Default value
        
        Example:
            # Add column
            schema.alter_table("users", "add_column", 
                             column_name="phone", 
                             column_type="VARCHAR(20)")
            
            # Rename column
            schema.alter_table("users", "rename_column",
                             column_name="phone",
                             new_column_name="mobile")
        """
        url = f"{self.base_url}/api/v2/schema/tables/{table_name}"
        
        payload = {
            "table_name": table_name,
            "operation": operation,
            "column_name": column_name,
            "column_type": column_type,
            "new_column_name": new_column_name,
            "nullable": nullable,
            "default": default
        }
        
        try:
            response = requests.patch(url, json=payload, headers=self.headers)
            
            if response.status_code == 403:
                raise PermissionError(
                    "Schema operations require a SERVICE ROLE key."
                )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise PermissionError(str(e))
            raise WowSQLError(f"Failed to alter table: {str(e)}")
    
    def drop_table(self, table_name: str, cascade: bool = False) -> Dict[str, Any]:
        """
        Drop a table.
        
        ⚠️ WARNING: This operation cannot be undone!
        
        Args:
            table_name: Name of the table to drop
            cascade: Whether to drop with CASCADE
        
        Example:
            schema.drop_table("old_users")
        """
        url = f"{self.base_url}/api/v2/schema/tables/{table_name}"
        params = {"cascade": cascade}
        
        try:
            response = requests.delete(url, params=params, headers=self.headers)
            
            if response.status_code == 403:
                raise PermissionError(
                    "Schema operations require a SERVICE ROLE key."
                )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise PermissionError(str(e))
            raise WowSQLError(f"Failed to drop table: {str(e)}")
    
    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute raw SQL for schema operations.
        
        ⚠️ Only schema operations allowed (CREATE TABLE, ALTER TABLE, etc.)
        
        Args:
            sql: SQL statement to execute
        
        Example:
            schema.execute_sql('''
                CREATE TABLE products (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255) NOT NULL,
                    price DECIMAL(10,2)
                )
            ''')
        """
        url = f"{self.base_url}/api/v2/schema/execute"
        
        payload = {"sql": sql}
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            
            if response.status_code == 403:
                raise PermissionError(
                    "Schema operations require a SERVICE ROLE key."
                )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                raise PermissionError(str(e))
            raise WowSQLError(f"Failed to execute SQL: {str(e)}")
