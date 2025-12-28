"""MySQL database connector."""

from typing import List, Dict, Any, Optional
import pymysql
from pymysql.cursors import DictCursor

from .base import BaseConnector


class MySQLConnector(BaseConnector):
    """MySQL database connector implementation."""
    
    def connect(self) -> bool:
        """Establish connection to MySQL."""
        try:
            self._connection = pymysql.connect(
                host=self.config.get("host"),
                port=self.config.get("port", 3306),
                user=self.config.get("username"),
                password=self.config.get("password"),
                database=self.config.get("database"),
                cursorclass=DictCursor,
                connect_timeout=10
            )
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MySQL: {str(e)}")
    
    def disconnect(self) -> None:
        """Close MySQL connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test MySQL connection."""
        try:
            self.connect()
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT VERSION() as version")
                result = cursor.fetchone()
            self.disconnect()
            return {
                "success": True,
                "message": "Connection successful",
                "details": {"version": result["version"]}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": None
            }
    
    def get_databases(self) -> List[str]:
        """List all databases."""
        with self._connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            return [row["Database"] for row in cursor.fetchall()]
    
    def get_schemas(self, database: str) -> List[str]:
        """MySQL doesn't have schemas, return database name."""
        return [database]
    
    def get_tables(self, database: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tables in a database."""
        with self._connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    TABLE_NAME as name,
                    TABLE_ROWS as row_count,
                    DATA_LENGTH + INDEX_LENGTH as size_bytes
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s
                AND TABLE_TYPE = 'BASE TABLE'
            """, (database,))
            return cursor.fetchall()
    
    def get_table_schema(
        self, database: str, table: str, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get column definitions for a table."""
        with self._connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME as name,
                    DATA_TYPE as data_type,
                    COLUMN_TYPE as full_type,
                    IS_NULLABLE as nullable,
                    COLUMN_KEY as key_type,
                    COLUMN_DEFAULT as default_value
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (database, table))
            columns = cursor.fetchall()
            return [
                {
                    "name": col["name"],
                    "data_type": col["full_type"],
                    "nullable": col["nullable"] == "YES",
                    "primary_key": col["key_type"] == "PRI",
                    "default": col["default_value"]
                }
                for col in columns
            ]
    
    def get_row_count(
        self, 
        database: str, 
        table: str, 
        schema: Optional[str] = None,
        where_clause: Optional[str] = None
    ) -> int:
        """Get row count for a table."""
        query = f"SELECT COUNT(*) as cnt FROM `{database}`.`{table}`"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        with self._connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            return result["cnt"]
    
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
        results = {}
        
        for col in columns:
            agg_parts = []
            for agg in aggregates:
                if agg == "COUNT_DISTINCT":
                    agg_parts.append(f"COUNT(DISTINCT `{col}`) as count_distinct")
                else:
                    agg_parts.append(f"{agg}(`{col}`) as {agg.lower()}")
            
            query = f"SELECT {', '.join(agg_parts)} FROM `{database}`.`{table}`"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            with self._connection.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                results[col] = {k.upper(): v for k, v in row.items()}
        
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
        col_str = ", ".join([f"`{c}`" for c in columns]) if columns else "*"
        query = f"SELECT {col_str} FROM `{database}`.`{table}`"
        
        if order_by:
            query += f" ORDER BY {', '.join([f'`{c}`' for c in order_by])}"
        
        query += f" LIMIT {limit}"
        
        with self._connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if rows:
                column_names = list(rows[0].keys())
                return {
                    "columns": column_names,
                    "rows": [list(row.values()) for row in rows],
                    "sample_size": len(rows)
                }
            return {"columns": [], "rows": [], "sample_size": 0}
    
    def search_tables(
        self, 
        pattern: str, 
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for tables matching a pattern."""
        with self._connection.cursor() as cursor:
            query = """
                SELECT 
                    TABLE_SCHEMA as database_name,
                    TABLE_NAME as name,
                    TABLE_ROWS as row_count
                FROM information_schema.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_NAME LIKE %s
            """
            params = [f"%{pattern}%"]
            
            if database:
                query += " AND TABLE_SCHEMA = %s"
                params.append(database)
            
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_table_stats(
        self,
        database: str,
        table: str,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get table statistics."""
        with self._connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    TABLE_ROWS as row_count,
                    DATA_LENGTH + INDEX_LENGTH as size_bytes,
                    UPDATE_TIME as last_updated
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """, (database, table))
            stats = cursor.fetchone()
            
            # Get column count
            cursor.execute(f"""
                SELECT COUNT(*) as col_count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """, (database, table))
            col_result = cursor.fetchone()
            
            return {
                "row_count": stats["row_count"] or 0,
                "column_count": col_result["col_count"],
                "size_bytes": stats["size_bytes"],
                "last_updated": stats["last_updated"]
            }
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        with self._connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
