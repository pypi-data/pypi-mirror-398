#!/usr/bin/env python3
"""MCP Server for Data Reconciliation.

This server exposes data reconciliation tools via the Model Context Protocol,
allowing LLM agents like Antigravity to perform data validation tasks.
"""

import asyncio
import json
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Prompt, PromptMessage, PromptArgument

from .tools import DataReconTools, TOOL_DEFINITIONS


# =============================================================================
# SERVER INSTRUCTIONS - Guides LLM behavior
# =============================================================================

SERVER_INSTRUCTIONS = """
# Data Reconciliation MCP Server

You are a Data Reconciliation assistant. Your role is to help users validate and 
compare data between MySQL and Snowflake databases to ensure data integrity during 
migrations, ETL processes, or ongoing data quality monitoring.

## PURPOSE
This server provides tools to:
- Register and manage database connections (MySQL, Snowflake)
- Discover tables and understand database schemas
- Run data validation checks (row counts, aggregates, schema comparison, sample rows)
- Execute comprehensive reconciliation jobs with progress tracking

## CRITICAL WORKFLOW RULES (GUARDRAILS)

### 1. ALWAYS DISCOVER BEFORE ACTING
Before running any reconciliation:
- Use `get_metadata_catalog` or `search_tables` to find the user's tables
- NEVER assume table names - always search and confirm
- Present options to the user if multiple matches exist

### 2. ALWAYS VALIDATE BEFORE CHECKING
Before running any check (row_count, aggregate, schema, sample):
- Use `validate_table_exists` to confirm both source and target tables exist
- For aggregate checks, use `validate_columns_exist` to verify columns are valid
- This prevents errors and wasted time

### 3. PREVIEW DATA WHEN UNCERTAIN
- Use `get_sample_data` to show users what's in a table
- This helps confirm you found the correct table
- Use `get_table_stats` for quick row count verification

### 4. COMPARE STRUCTURES FIRST
Before running data checks:
- Use `compare_table_structures` to see schema differences
- This helps users understand if type conversions might cause false mismatches

### 5. PREFER FULL RECONCILIATION JOBS
- **STRONGLY PREFER** `create_recon_job` over running individual checks manually.
- Use `create_recon_job` to run all necessary checks (row_count, schema, aggregates, sample_rows) in a single background process.
- **DO NOT** run individual check tools (`run_row_count_check`, `run_aggregate_check`, etc.) unless the user *specifically* asks for a single, isolated check.
- **DO NOT** auto-run checks immediately after discovery. ALWAYS ask the user for confirmation before starting a job.

### 6. RECOMMENDED WORKFLOW
```
1. User: "Compare orders table"
2. YOU: Search and confirm table names (search_tables)
3. YOU: Validate existence (validate_table_exists) & Compare structure (compare_table_structures)
4. YOU: "I found the tables. Shall I run a full reconciliation job?"
5. USER: "Yes"
6. YOU: call create_recon_job(checks=[row_count, schema, aggregates, sample])
7. YOU: Poll status until complete
```

### 7. HANDLE LARGE TABLES WITH PARTITIONING
For tables with millions of rows:
- Suggest using `partition_config` to compare date ranges
- Example: Compare only last 7 days of data

## RECOMMENDED WORKFLOW

```
1. User: "Compare orders table between MySQL and Snowflake"

2. YOU: Search for tables in both sources
   → search_tables(datasource="mysql_prod", pattern="order")
   → search_tables(datasource="snowflake_dw", pattern="order")

3. YOU: Present matches and ask user to confirm
   → "I found these tables. Which should I compare?"

4. USER: Confirms tables

5. YOU: Validate tables exist
   → validate_table_exists(...)
   → compare_table_structures(...)

6. YOU: Show user the structure comparison
   → "Source has 15 columns, target has 14. Column X is missing in target."

7. YOU: Run checks (starting with row count)
   → run_row_count_check(...)
   → run_aggregate_check(...) if numeric columns exist
   → run_sample_check(...) for detailed validation

8. YOU: Report results clearly
   → "Row counts match (1.5M rows). SUM(amount) differs by $0.02..."
```

## ERROR HANDLING
- If a data source is not registered, suggest using `add_datasource`
- If connection fails, suggest checking credentials with `test_datasource`
- If tables not found, use `search_tables` with broader patterns

## BEST PRACTICES
- Always explain what you're checking and why
- Report both matches AND mismatches clearly
- For mismatches, suggest possible causes (data type differences, timezone issues, etc.)
- Recommend next steps based on results
"""


# =============================================================================
# PROMPTS - Reusable prompt templates for common workflows
# =============================================================================

PROMPTS = [
    {
        "name": "quick_validation",
        "description": "Quick validation workflow for comparing two tables",
        "arguments": [
            {"name": "source_datasource", "description": "Source data source name", "required": True},
            {"name": "target_datasource", "description": "Target data source name", "required": True},
            {"name": "table_pattern", "description": "Table name or pattern to search for", "required": True}
        ],
        "template": """
I need to perform a quick data validation with these parameters:
- Source data source: {source_datasource}
- Target data source: {target_datasource}
- Table to find: {table_pattern}

Please follow the standard workflow:
1. Search for the table in both data sources
2. Confirm the exact tables with me
3. Validate the tables exist
4. Run a row count check first
5. If counts match, run an aggregate check on numeric columns
6. Report results clearly
"""
    },
    {
        "name": "full_reconciliation",
        "description": "Comprehensive reconciliation job with all check types",
        "arguments": [
            {"name": "source_table", "description": "Full source table reference", "required": True},
            {"name": "target_table", "description": "Full target table reference", "required": True},
            {"name": "primary_key", "description": "Primary key column(s) for sample comparison", "required": True}
        ],
        "template": """
I need a comprehensive data reconciliation:
- Source: {source_table}
- Target: {target_table}
- Primary key for row matching: {primary_key}

Please:
1. Validate both tables exist
2. Compare table structures first
3. Create a reconciliation job with ALL check types:
   - row_count
   - schema
   - aggregates (on all numeric columns)
   - sample_rows (using the provided primary key)
4. Monitor job progress and report results
"""
    },
    {
        "name": "setup_datasources",
        "description": "Help setting up new data source connections",
        "arguments": [],
        "template": """
I need help setting up database connections for data reconciliation.

Please:
1. List any existing data sources with list_datasources
2. Guide me through adding a new data source:
   - Ask what type (MySQL or Snowflake)
   - Ask for connection details
   - Use add_datasource to register it
   - Test the connection with test_datasource
   - Show available databases with get_databases
"""
    }
]


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("data-recon")
    tools = DataReconTools()
    
    # Set server instructions for LLM guidance
    server.instructions = SERVER_INSTRUCTIONS
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available tools."""
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"]
            )
            for t in TOOL_DEFINITIONS
        ]
    
    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """List available prompt templates."""
        return [
            Prompt(
                name=p["name"],
                description=p["description"],
                arguments=[
                    PromptArgument(
                        name=arg["name"],
                        description=arg["description"],
                        required=arg.get("required", False)
                    )
                    for arg in p["arguments"]
                ]
            )
            for p in PROMPTS
        ]
    
    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> list[PromptMessage]:
        """Get a prompt template with arguments filled in."""
        for p in PROMPTS:
            if p["name"] == name:
                template = p["template"]
                if arguments:
                    template = template.format(**arguments)
                return [
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=template)
                    )
                ]
        raise ValueError(f"Prompt not found: {name}")
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute a tool and return the result."""
        import sys
        from datetime import datetime
        
        def log(msg):
            timestamp = datetime.now().isoformat()
            print(f"[{timestamp}] [TOOL] {msg}", file=sys.stderr, flush=True)
            # Also log to file
            try:
                log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "mcp_server.log")
                with open(log_file, "a") as f:
                    f.write(f"[{timestamp}] [TOOL] {msg}\n")
            except:
                pass
        
        log(f"Received tool call: {name}")
        log(f"Arguments: {json.dumps(arguments, default=str)}")
        
        try:
            # Get the method from DataReconTools
            method = getattr(tools, name, None)
            if not method:
                log(f"ERROR: Unknown tool: {name}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"})
                )]
            
            log(f"Calling method: {name}")
            # Call the method with arguments
            result = method(**arguments)
            log(f"Method returned successfully")
            
            # Add helpful hints based on results
            result = add_result_hints(name, result)
            
            log(f"Tool call completed: {name}")
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except Exception as e:
            log(f"ERROR in tool {name}: {str(e)}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "hint": get_error_hint(name, str(e))
                })
            )]
    
    return server


def add_result_hints(tool_name: str, result: dict) -> dict:
    """Add helpful hints to tool results to guide LLM behavior."""
    hints = []
    
    if tool_name == "list_datasources":
        if not result or len(result) == 0:
            hints.append("No data sources registered. Use add_datasource to register one.")
    
    elif tool_name == "validate_table_exists":
        if not result.get("exists"):
            hints.append("Table not found. Use search_tables to find similar tables.")
    
    elif tool_name == "validate_columns_exist":
        if not result.get("all_exist"):
            missing = result.get("missing", [])
            hints.append(f"Missing columns: {missing}. Verify column names with get_table_schema.")
    
    elif tool_name == "run_row_count_check":
        if not result.get("match"):
            diff = result.get("difference", 0)
            hints.append(f"Row count mismatch of {diff} rows. Consider using sample_check to identify missing rows.")
    
    elif tool_name == "run_aggregate_check":
        if not result.get("all_match"):
            hints.append("Aggregate mismatch. This could be due to data type precision, missing rows, or data transformation differences.")
    
    elif tool_name == "run_schema_check":
        if not result.get("match"):
            hints.append("Schema mismatch. Review type_differences for potential data conversion issues.")
    
    elif tool_name == "compare_table_structures":
        if not result.get("structures_match"):
            hints.append("Structures differ. This may cause aggregate mismatches - proceed with caution.")
    
    elif tool_name == "search_tables":
        if result.get("total_matches", 0) == 0:
            hints.append("No tables found. Try a broader search pattern or check the database name.")
        elif result.get("total_matches", 0) > 1:
            hints.append("Multiple matches found. Confirm with user which table to use.")
    
    if hints:
        result["_hints"] = hints
    
    return result


def get_error_hint(tool_name: str, error: str) -> str:
    """Provide helpful hints for common errors."""
    error_lower = error.lower()
    
    if "not found" in error_lower:
        if "data source" in error_lower:
            return "Data source not registered. Use list_datasources to see available sources, or add_datasource to register a new one."
        elif "table" in error_lower:
            return "Table not found. Use search_tables to find the correct table name."
    
    if "connection" in error_lower or "connect" in error_lower:
        return "Connection failed. Use test_datasource to verify credentials and network connectivity."
    
    if "permission" in error_lower or "access denied" in error_lower:
        return "Permission denied. Check that the database user has read access to the table."
    
    if "timeout" in error_lower:
        return "Query timeout. For large tables, consider using partition_config to query smaller date ranges."
    
    return "Check the error message and verify input parameters."


async def register_preconfigured_datasources():
    """Register data sources from environment variables on startup."""
    tools = DataReconTools()
    
    for key, value in os.environ.items():
        if key.startswith("DATASOURCE_"):
            try:
                # Extract name from env var (e.g., DATASOURCE_MYSQL_PROD -> mysql_prod)
                name = key[11:].lower()  # Remove "DATASOURCE_" prefix
                config = json.loads(value)
                ds_type = config.pop("type", "mysql")
                
                # Try to register (may already exist)
                try:
                    tools.add_datasource(name, ds_type, config)
                    print(f"Registered pre-configured data source: {name}", file=sys.stderr)
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"Warning: Could not register {name}: {e}", file=sys.stderr)
                        
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON in {key}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Error processing {key}: {e}", file=sys.stderr)


async def main():
    """Main entry point for the MCP server."""
    # Register pre-configured data sources
    await register_preconfigured_datasources()
    
    # Create and run server
    server = create_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


# =============================================================================
# EMBEDDED FASTAPI SERVER - For all-in-one distribution
# =============================================================================

def start_embedded_backend(host: str = "127.0.0.1", port: int = 8000):
    """Start the FastAPI backend in a background thread.
    
    This allows the MCP server to be fully self-contained - users don't need
    to run a separate backend process.
    """
    import threading
    import time
    import uvicorn
    import httpx
    
    # Import the FastAPI app
    from data_recon.main import app
    from data_recon.database import init_db
    
    # Initialize database tables
    init_db()
    
    # Configure uvicorn to run silently (no access logs cluttering stderr)
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",  # Suppress info logs
        access_log=False,
    )
    server = uvicorn.Server(config)
    
    # Run in a daemon thread so it dies when the main process exits
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    
    # Wait for the server to be ready (max 10 seconds)
    for i in range(100):
        try:
            with httpx.Client(timeout=1.0) as client:
                response = client.get(f"http://{host}:{port}/health")
                if response.status_code == 200:
                    print(f"[data-recon] Backend ready at http://{host}:{port}", file=sys.stderr)
                    return True
        except:
            pass
        time.sleep(0.1)
    
    print("[data-recon] WARNING: Backend may not be ready", file=sys.stderr)
    return False


def run():
    """Entry point for pip-installed command 'data-recon-server'.
    
    This is the all-in-one entry point that:
    1. Starts the FastAPI backend automatically
    2. Runs the MCP server
    3. Cleans up when done
    """
    import os
    
    # Check if user wants to use an external backend
    external_url = os.environ.get("FASTAPI_URL")
    
    if external_url:
        # User provided an external backend URL - use it
        print(f"[data-recon] Using external backend: {external_url}", file=sys.stderr)
    else:
        # Start embedded backend
        print("[data-recon] Starting embedded backend...", file=sys.stderr)
        
        # Set the environment variable so tools.py knows where to connect
        os.environ["FASTAPI_URL"] = "http://127.0.0.1:8000"
        
        # Start the backend
        if not start_embedded_backend():
            print("[data-recon] Failed to start backend", file=sys.stderr)
            sys.exit(1)
    
    # Run the MCP server
    asyncio.run(main())


if __name__ == "__main__":
    run()
