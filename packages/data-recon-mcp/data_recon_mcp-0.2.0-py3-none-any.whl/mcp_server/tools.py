"""Tool definitions for the MCP server with enhanced descriptions for LLM guidance."""

from typing import Dict, Any, List
import httpx
import os
import time
import sys

# FastAPI server URL
FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://localhost:8000")

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds


def log_stderr(msg: str):
    """Log to stderr for debugging (stdout is for JSON-RPC)."""
    print(f"[MCP-TOOLS] {msg}", file=sys.stderr)


class DataReconTools:
    """Tools for data reconciliation operations."""
    
    def __init__(self):
        self.client = httpx.Client(base_url=FASTAPI_URL, timeout=60.0)
    
    def _request_with_retry(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic for transient failures."""
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                if method == "GET":
                    response = self.client.get(path, **kwargs)
                elif method == "POST":
                    response = self.client.post(path, **kwargs)
                elif method == "DELETE":
                    response = self.client.delete(path, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.ConnectError as e:
                last_error = e
                log_stderr(f"Connection failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            except httpx.HTTPStatusError as e:
                # Don't retry on HTTP errors (4xx, 5xx) - these are expected errors
                raise
            except Exception as e:
                last_error = e
                log_stderr(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        
        raise ConnectionError(
            f"Failed to connect to FastAPI at {FASTAPI_URL} after {MAX_RETRIES} attempts. "
            f"Is the backend running? Last error: {last_error}"
        )
    
    def _get(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make GET request to FastAPI with retry."""
        return self._request_with_retry("GET", path, params=params)
    
    def _post(self, path: str, json: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make POST request to FastAPI with retry."""
        return self._request_with_retry("POST", path, json=json, params=params)
    
    def _delete(self, path: str) -> Dict[str, Any]:
        """Make DELETE request to FastAPI with retry."""
        return self._request_with_retry("DELETE", path)
    
    # ========== DATA SOURCE MANAGEMENT ==========
    
    def add_datasource(self, name: str, type: str, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new database connection."""
        return self._post("/datasources", json={
            "name": name,
            "type": type,
            "connection_config": connection_config
        })
    
    def list_datasources(self) -> List[Dict[str, Any]]:
        """List all registered data sources."""
        return self._get("/datasources")
    
    def test_datasource(self, datasource_name: str) -> Dict[str, Any]:
        """Validate connection to a data source."""
        return self._post(f"/datasources/{datasource_name}/test")
    
    def remove_datasource(self, datasource_name: str) -> Dict[str, Any]:
        """Remove a registered data source."""
        return self._delete(f"/datasources/{datasource_name}")
    
    def get_databases(self, datasource_name: str) -> Dict[str, Any]:
        """List databases in a data source."""
        return self._get(f"/datasources/{datasource_name}/databases")
    
    def get_tables(self, datasource_name: str, database: str, schema: str = None) -> Dict[str, Any]:
        """List tables in a database/schema."""
        params = {"database": database}
        if schema:
            params["schema"] = schema
        return self._get(f"/datasources/{datasource_name}/tables", params)
    
    def get_table_schema(self, datasource_name: str, database: str, table: str, schema: str = None) -> Dict[str, Any]:
        """Get column definitions for a table."""
        params = {"database": database, "table": table}
        if schema:
            params["schema"] = schema
        return self._get(f"/datasources/{datasource_name}/schema", params)
    
    # ========== DISCOVERY & VALIDATION ==========
    
    def get_metadata_catalog(self, datasource_name: str) -> Dict[str, Any]:
        """Get full metadata catalog for a data source."""
        return self._get(f"/datasources/{datasource_name}/catalog")
    
    def search_tables(self, datasource_name: str, pattern: str, database: str = None) -> Dict[str, Any]:
        """Search for tables matching a pattern."""
        params = {"pattern": pattern}
        if database:
            params["database"] = database
        return self._get(f"/datasources/{datasource_name}/search", params)
    
    def get_sample_data(self, datasource_name: str, database: str, table: str, 
                        schema: str = None, limit: int = 10) -> Dict[str, Any]:
        """Get sample data from a table."""
        params = {"database": database, "table": table, "limit": limit}
        if schema:
            params["schema"] = schema
        return self._get(f"/datasources/{datasource_name}/sample", params)
    
    def validate_table_exists(self, datasource_name: str, database: str, 
                              table: str, schema: str = None) -> Dict[str, Any]:
        """Validate that a table exists."""
        params = {"database": database, "table": table}
        if schema:
            params["schema"] = schema
        return self._get(f"/datasources/{datasource_name}/validate/table", params)
    
    def validate_columns_exist(self, datasource_name: str, database: str, table: str,
                               columns: List[str], schema: str = None) -> Dict[str, Any]:
        """Validate that columns exist in a table."""
        params = {"database": database, "table": table, "columns": columns}
        if schema:
            params["schema"] = schema
        return self._post(f"/datasources/{datasource_name}/validate/columns", params=params)
    
    def get_table_stats(self, datasource_name: str, database: str, 
                        table: str, schema: str = None) -> Dict[str, Any]:
        """Get table statistics."""
        params = {"database": database, "table": table}
        if schema:
            params["schema"] = schema
        return self._get(f"/datasources/{datasource_name}/stats", params)
    
    def compare_table_structures(self, source_datasource: str, source_database: str,
                                 source_table: str, source_schema: str,
                                 target_datasource: str, target_database: str,
                                 target_table: str, target_schema: str) -> Dict[str, Any]:
        """Compare table structures side by side."""
        params = {
            "source_datasource": source_datasource,
            "source_database": source_database,
            "source_table": source_table,
            "source_schema": source_schema,
            "target_datasource": target_datasource,
            "target_database": target_database,
            "target_table": target_table,
            "target_schema": target_schema
        }
        return self._post("/datasources/compare-structures", params=params)
    
    # ========== INDIVIDUAL CHECKS ==========
    
    def run_row_count_check(self, source: Dict[str, Any], target: Dict[str, Any],
                            partition_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a quick row count comparison."""
        return self._post("/jobs/checks/row-count", json={
            "source": source,
            "target": target,
            "partition_config": partition_config
        })
    
    def run_aggregate_check(self, source: Dict[str, Any], target: Dict[str, Any],
                            columns: List[str], aggregates: List[str] = None,
                            partition_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run column-level aggregate comparison."""
        return self._post("/jobs/checks/aggregates", json={
            "source": source,
            "target": target,
            "columns": columns,
            "aggregates": aggregates or ["SUM"],
            "partition_config": partition_config
        })
    
    def run_schema_check(self, source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        """Run schema comparison."""
        return self._post("/jobs/checks/schema", json={
            "source": source,
            "target": target
        })
    
    def run_sample_check(self, source: Dict[str, Any], target: Dict[str, Any],
                         primary_key: List[str], sample_size: int = 100,
                         columns: List[str] = None) -> Dict[str, Any]:
        """Run sample row comparison."""
        return self._post("/jobs/checks/sample", json={
            "source": source,
            "target": target,
            "primary_key": primary_key,
            "sample_size": sample_size,
            "columns": columns
        })
    
    # ========== JOB MANAGEMENT ==========
    
    def create_recon_job(self, source: Dict[str, Any], target: Dict[str, Any],
                         checks: List[Dict[str, Any]], 
                         partition_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a full reconciliation job with multiple checks."""
        return self._post("/jobs", json={
            "source": source,
            "target": target,
            "checks": checks,
            "partition_config": partition_config
        })
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status with progress indicator."""
        return self._get(f"/jobs/{job_id}/status")
    
    def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """Get detailed job results."""
        return self._get(f"/jobs/{job_id}/results")
    
    def list_jobs(self, limit: int = 20, status_filter: str = None) -> List[Dict[str, Any]]:
        """List recent jobs."""
        params = {"limit": limit}
        if status_filter:
            params["status"] = status_filter
        return self._get("/jobs", params)
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running job."""
        return self._post(f"/jobs/{job_id}/cancel")


# =============================================================================
# TOOL DEFINITIONS with enhanced descriptions for LLM guidance
# =============================================================================

TOOL_DEFINITIONS = [
    # =========================================================================
    # DATA SOURCE MANAGEMENT (7 tools)
    # =========================================================================
    {
        "name": "add_datasource",
        "description": "Register a new database connection (MySQL or Snowflake). AFTER USING: Always call test_datasource to verify the connection works. MySQL config: {host, port, username, password, database}. Snowflake config: {account, username, password, warehouse, database, schema}.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Unique name for this data source (e.g., 'mysql_prod', 'snowflake_dw')"},
                "type": {"type": "string", "enum": ["mysql", "snowflake"], "description": "Database type"},
                "connection_config": {"type": "object", "description": "Connection configuration object"}
            },
            "required": ["name", "type", "connection_config"]
        }
    },
    {
        "name": "list_datasources",
        "description": "List all registered data sources. FIRST STEP: Always check what data sources are available before doing any work. If empty, guide user to add data sources with add_datasource.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "test_datasource",
        "description": "Test connection to a data source. USE: After adding a new data source, when user reports issues, or before starting reconciliation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string", "description": "Name of the data source to test"}
            },
            "required": ["datasource_name"]
        }
    },
    {
        "name": "remove_datasource",
        "description": "Remove a registered data source. CAUTION: This deletes the configuration permanently.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string", "description": "Name of the data source to remove"}
            },
            "required": ["datasource_name"]
        }
    },
    {
        "name": "get_databases",
        "description": "List all databases in a data source. USE: To discover available databases before listing tables.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string", "description": "Name of the data source"}
            },
            "required": ["datasource_name"]
        }
    },
    {
        "name": "get_tables",
        "description": "List all tables in a database/schema. PREFER search_tables if user mentions a specific table name pattern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string"},
                "database": {"type": "string"},
                "schema": {"type": "string", "description": "Schema name (required for Snowflake)"}
            },
            "required": ["datasource_name", "database"]
        }
    },
    {
        "name": "get_table_schema",
        "description": "Get column definitions (name, type, nullable, primary key). USE: To understand table structure, find numeric columns for aggregates, or find primary keys for sample checks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string"},
                "database": {"type": "string"},
                "table": {"type": "string"},
                "schema": {"type": "string"}
            },
            "required": ["datasource_name", "database", "table"]
        }
    },
    
    # =========================================================================
    # DISCOVERY & VALIDATION (7 tools) - ANTI-HALLUCINATION GUARDRAILS
    # =========================================================================
    {
        "name": "get_metadata_catalog",
        "description": "Get FULL metadata catalog (all databases, schemas, tables). USE: When starting with a data source to understand what's available. WARNING: Can be slow for large databases - prefer search_tables for targeted queries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string"}
            },
            "required": ["datasource_name"]
        }
    },
    {
        "name": "search_tables",
        "description": "🔍 CRITICAL - USE FIRST when user mentions a table name. Search for tables by name pattern. NEVER assume table names exist - always search first. Example: User says 'orders table' → search pattern 'order' to find 'orders', 'order_items', etc. Then confirm with user which table they mean.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string"},
                "pattern": {"type": "string", "description": "Search pattern - matches any table containing this text"},
                "database": {"type": "string", "description": "Optional: limit search to specific database"}
            },
            "required": ["datasource_name", "pattern"]
        }
    },
    {
        "name": "get_sample_data",
        "description": "Preview first N rows of a table. USE: To VERIFY you found the correct table before running expensive checks. Show user what data looks like.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string"},
                "database": {"type": "string"},
                "table": {"type": "string"},
                "schema": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["datasource_name", "database", "table"]
        }
    },
    {
        "name": "validate_table_exists",
        "description": "⚠️ REQUIRED BEFORE CHECKS - Verify a table exists before running any reconciliation. ALWAYS call this for BOTH source AND target tables before run_row_count_check, run_aggregate_check, run_schema_check, or run_sample_check. Prevents wasted time and cryptic errors.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string"},
                "database": {"type": "string"},
                "table": {"type": "string"},
                "schema": {"type": "string"}
            },
            "required": ["datasource_name", "database", "table"]
        }
    },
    {
        "name": "validate_columns_exist",
        "description": "⚠️ REQUIRED FOR AGGREGATES - Verify columns exist before running aggregate checks. ALWAYS call this before run_aggregate_check to prevent errors from typos or missing columns.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string"},
                "database": {"type": "string"},
                "table": {"type": "string"},
                "columns": {"type": "array", "items": {"type": "string"}},
                "schema": {"type": "string"}
            },
            "required": ["datasource_name", "database", "table", "columns"]
        }
    },
    {
        "name": "get_table_stats",
        "description": "Get quick statistics: row count, column count, size. USE: For sanity check before reconciliation, to estimate how long checks might take (large tables = longer).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datasource_name": {"type": "string"},
                "database": {"type": "string"},
                "table": {"type": "string"},
                "schema": {"type": "string"}
            },
            "required": ["datasource_name", "database", "table"]
        }
    },
    {
        "name": "compare_table_structures",
        "description": "📊 RECOMMENDED FIRST STEP - Side-by-side comparison of source and target schemas BEFORE running data checks. Shows column differences and type mismatches that may cause false positives in data comparison.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_datasource": {"type": "string"},
                "source_database": {"type": "string"},
                "source_table": {"type": "string"},
                "source_schema": {"type": "string"},
                "target_datasource": {"type": "string"},
                "target_database": {"type": "string"},
                "target_table": {"type": "string"},
                "target_schema": {"type": "string"}
            },
            "required": ["source_datasource", "source_database", "source_table", 
                        "target_datasource", "target_database", "target_table"]
        }
    },
    
    # =========================================================================
    # INDIVIDUAL CHECKS (4 tools) - Run AFTER validation
    # =========================================================================
    {
        "name": "run_row_count_check",
        "description": "✅ FAST FIRST CHECK - Compare row counts. Run this FIRST - it's fast and catches major issues. PREREQUISITE: Call validate_table_exists for both tables first. For large tables, use partition_config to compare date ranges.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "object",
                    "properties": {
                        "datasource": {"type": "string"},
                        "database": {"type": "string"},
                        "schema": {"type": "string"},
                        "table": {"type": "string"}
                    },
                    "required": ["datasource", "database", "table"]
                },
                "target": {
                    "type": "object",
                    "properties": {
                        "datasource": {"type": "string"},
                        "database": {"type": "string"},
                        "schema": {"type": "string"},
                        "table": {"type": "string"}
                    },
                    "required": ["datasource", "database", "table"]
                },
                "partition_config": {
                    "type": "object",
                    "description": "Optional: {column, start_value, end_value} for incremental comparison"
                }
            },
            "required": ["source", "target"]
        }
    },
    {
        "name": "run_aggregate_check",
        "description": "Compare column-level aggregates: SUM, AVG, MIN, MAX, COUNT_DISTINCT. PREREQUISITES: 1) validate_table_exists 2) validate_columns_exist. USE: After row counts match, to verify numeric data integrity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "object"},
                "target": {"type": "object"},
                "columns": {"type": "array", "items": {"type": "string"}, "description": "Numeric columns to aggregate"},
                "aggregates": {
                    "type": "array", 
                    "items": {"type": "string", "enum": ["SUM", "AVG", "MIN", "MAX", "COUNT_DISTINCT"]},
                    "default": ["SUM"]
                },
                "partition_config": {"type": "object"}
            },
            "required": ["source", "target", "columns"]
        }
    },
    {
        "name": "run_schema_check",
        "description": "Compare table schemas (column names, data types). USE: To identify structural differences that might cause data issues.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "object"},
                "target": {"type": "object"}
            },
            "required": ["source", "target"]
        }
    },
    {
        "name": "run_sample_check",
        "description": "🔬 DETAILED CHECK - Compare actual row values by primary key. USE: After row counts and aggregates pass, for detailed validation. Identifies specific mismatched rows. PREREQUISITE: validate_table_exists, know the primary key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "object"},
                "target": {"type": "object"},
                "primary_key": {"type": "array", "items": {"type": "string"}},
                "sample_size": {"type": "integer", "default": 100},
                "columns": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["source", "target", "primary_key"]
        }
    },
    
    # =========================================================================
    # JOB MANAGEMENT (5 tools) - For comprehensive reconciliation
    # =========================================================================
    {
        "name": "create_recon_job",
        "description": "Create comprehensive reconciliation job with multiple checks. Runs asynchronously - use get_job_status to monitor. PREREQUISITES: validate_table_exists, compare_table_structures.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "object"},
                "target": {"type": "object"},
                "checks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["row_count", "aggregates", "schema", "sample_rows"]},
                            "columns": {"type": "array", "items": {"type": "string"}},
                            "aggregates": {"type": "array", "items": {"type": "string"}},
                            "primary_key": {"type": "array", "items": {"type": "string"}},
                            "sample_size": {"type": "integer"}
                        },
                        "required": ["type"]
                    }
                },
                "partition_config": {"type": "object"}
            },
            "required": ["source", "target", "checks"]
        }
    },
    {
        "name": "get_job_status",
        "description": "Get job progress: status, percent complete, current check. Poll every few seconds while running. Report to user: 'Job is 50% complete, running aggregate check...'",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "get_job_results",
        "description": "Get detailed results after job completes. USE: After get_job_status shows status=completed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "list_jobs",
        "description": "List recent reconciliation jobs. USE: To see job history or find previous results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20},
                "status_filter": {"type": "string", "enum": ["pending", "running", "completed", "failed", "cancelled"]}
            }
        }
    },
    {
        "name": "cancel_job",
        "description": "Cancel a running job. USE: When user wants to stop long-running reconciliation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"}
            },
            "required": ["job_id"]
        }
    }
]
