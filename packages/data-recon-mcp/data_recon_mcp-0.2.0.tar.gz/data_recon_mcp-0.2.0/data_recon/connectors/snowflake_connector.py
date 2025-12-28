"""Snowflake database connector."""

from typing import List, Dict, Any, Optional
import snowflake.connector

from .base import BaseConnector


class SnowflakeConnector(BaseConnector):
    """Snowflake database connector implementation."""
    
    def connect(self) -> bool:
        """Establish connection to Snowflake."""
        try:
            self._connection = snowflake.connector.connect(
                account=self.config.get("account"),
                user=self.config.get("username"),
                password=self.config.get("password"),
                warehouse=self.config.get("warehouse"),
                database=self.config.get("database"),
                schema=self.config.get("schema_name") or self.config.get("schema"),
                role=self.config.get("role"),
                login_timeout=10
            )
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Snowflake: {str(e)}")
    
    def disconnect(self) -> None:
        """Close Snowflake connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Snowflake connection."""
        try:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT CURRENT_VERSION() as version")
            result = cursor.fetchone()
            cursor.close()
            self.disconnect()
            return {
                "success": True,
                "message": "Connection successful",
                "details": {"version": result[0]}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": None
            }
    
    def get_databases(self) -> List[str]:
        """List all databases."""
        cursor = self._connection.cursor()
        cursor.execute("SHOW DATABASES")
        results = cursor.fetchall()
        cursor.close()
        # Database name is typically in the second column
        return [row[1] for row in results]
    
    def get_schemas(self, database: str) -> List[str]:
        """List all schemas in a database."""
        cursor = self._connection.cursor()
        cursor.execute(f"SHOW SCHEMAS IN DATABASE {database}")
        results = cursor.fetchall()
        cursor.close()
        return [row[1] for row in results]
    
    def get_tables(self, database: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tables in a database/schema."""
        cursor = self._connection.cursor()
        
        if schema:
            cursor.execute(f"SHOW TABLES IN {database}.{schema}")
        else:
            cursor.execute(f"SHOW TABLES IN DATABASE {database}")
        
        results = cursor.fetchall()
        cursor.close()
        
        tables = []
        for row in results:
            tables.append({
                "name": row[1],  # TABLE_NAME
                "schema": row[3] if len(row) > 3 else schema,  # SCHEMA_NAME
                "row_count": row[5] if len(row) > 5 else None  # ROWS
            })
        return tables
    
    def get_table_schema(
        self, database: str, table: str, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get column definitions for a table."""
        cursor = self._connection.cursor()
        
        full_table = f"{database}.{schema}.{table}" if schema else f"{database}.{table}"
        cursor.execute(f"DESCRIBE TABLE {full_table}")
        results = cursor.fetchall()
        cursor.close()
        
        columns = []
        for row in results:
            columns.append({
                "name": row[0],
                "data_type": row[1],
                "nullable": row[3] == "Y",
                "primary_key": row[4] == "Y" if len(row) > 4 else False,
                "default": row[5] if len(row) > 5 else None
            })
        return columns
    
    def get_row_count(
        self, 
        database: str, 
        table: str, 
        schema: Optional[str] = None,
        where_clause: Optional[str] = None
    ) -> int:
        """Get row count for a table."""
        full_table = f"{database}.{schema}.{table}" if schema else f"{database}.{table}"
        query = f"SELECT COUNT(*) FROM {full_table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        cursor = self._connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        return result[0]
    
    def get_aggregates(
        self,
        database: str,
        table: str,
        columns: List[str],
        aggregates: List[str],
        schema: Optional[str] = None,
        where_clause: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get aggregate values for columns."""
        full_table = f"{database}.{schema}.{table}" if schema else f"{database}.{table}"
        results = {}
        
        for col in columns:
            agg_parts = []
            for agg in aggregates:
                if agg == "COUNT_DISTINCT":
                    agg_parts.append(f"COUNT(DISTINCT \"{col}\") as COUNT_DISTINCT")
                else:
                    agg_parts.append(f"{agg}(\"{col}\") as {agg}")
            
            query = f"SELECT {', '.join(agg_parts)} FROM {full_table}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            cursor = self._connection.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            description = cursor.description
            cursor.close()
            
            results[col] = {desc[0]: value for desc, value in zip(description, row)}
        
        return results
    
    def get_sample_rows(
        self,
        database: str,
        table: str,
        limit: int = 100,
        schema: Optional[str] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get sample rows from a table."""
        full_table = f"{database}.{schema}.{table}" if schema else f"{database}.{table}"
        col_str = ", ".join([f'"{c}"' for c in columns]) if columns else "*"
        query = f"SELECT {col_str} FROM {full_table}"
        
        if order_by:
            query += f" ORDER BY {', '.join([f'\"{c}\"' for c in order_by])}"
        
        query += f" LIMIT {limit}"
        
        cursor = self._connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        cursor.close()
        
        return {
            "columns": column_names,
            "rows": [list(row) for row in rows],
            "sample_size": len(rows)
        }
    
    def search_tables(
        self, 
        pattern: str, 
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for tables matching a pattern."""
        cursor = self._connection.cursor()
        
        if database:
            cursor.execute(f"SHOW TABLES LIKE '%{pattern}%' IN DATABASE {database}")
        else:
            cursor.execute(f"SHOW TABLES LIKE '%{pattern}%'")
        
        results = cursor.fetchall()
        cursor.close()
        
        tables = []
        for row in results:
            tables.append({
                "database_name": row[2] if len(row) > 2 else database,
                "name": row[1],
                "row_count": row[5] if len(row) > 5 else None
            })
        return tables
    
    def get_table_stats(
        self,
        database: str,
        table: str,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get table statistics."""
        full_table = f"{database}.{schema}.{table}" if schema else f"{database}.{table}"
        cursor = self._connection.cursor()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {full_table}")
        row_count = cursor.fetchone()[0]
        
        # Get column count
        cursor.execute(f"DESCRIBE TABLE {full_table}")
        columns = cursor.fetchall()
        
        cursor.close()
        
        return {
            "row_count": row_count,
            "column_count": len(columns),
            "size_bytes": None,  # Requires additional Snowflake queries
            "last_updated": None
        }
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        cursor = self._connection.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        return [dict(zip(columns, row)) for row in rows]
