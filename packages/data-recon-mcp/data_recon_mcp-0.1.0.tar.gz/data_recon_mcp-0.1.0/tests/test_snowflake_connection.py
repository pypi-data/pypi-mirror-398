"""
Test Snowflake Connection

This script validates that you can connect to Snowflake with your credentials.
It reads credentials from environment variables for security.

Usage:
    1. Set environment variables:
        export SNOWFLAKE_ACCOUNT="your-account-id"
        export SNOWFLAKE_USER="your-username"
        export SNOWFLAKE_PASSWORD="your-password"
        export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
        export SNOWFLAKE_DATABASE="SNOWFLAKE_SAMPLE_DATA"
        export SNOWFLAKE_SCHEMA="TPCDS_SF10TCL"
    
    2. Run the test:
        python tests/test_snowflake_connection.py
"""

import os
import sys

# Try to import snowflake connector
try:
    import snowflake.connector
except ImportError:
    print("ERROR: snowflake-connector-python not installed.")
    print("Install with: pip install snowflake-connector-python")
    sys.exit(1)


def get_config_from_env():
    """Load Snowflake config from environment variables."""
    config = {
        "account": os.environ.get("SNOWFLAKE_ACCOUNT", "your-org-your-account"),
        "user": os.environ.get("SNOWFLAKE_USER", "your-username"),
        "password": os.environ.get("SNOWFLAKE_PASSWORD", "your-password"),
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        "database": os.environ.get("SNOWFLAKE_DATABASE", "SNOWFLAKE_SAMPLE_DATA"),
        "schema": os.environ.get("SNOWFLAKE_SCHEMA", "TPCDS_SF10TCL"),
    }
    return config


def test_connection():
    """Test Snowflake connection with environment credentials."""
    config = get_config_from_env()
    
    # Check if using placeholder values
    if config["account"] == "your-org-your-account":
        print("WARNING: Using placeholder values. Set environment variables first!")
        print("See docstring at top of file for instructions.")
        print()
    
    print(f"Testing Snowflake connection...")
    print(f"  Account:   {config['account']}")
    print(f"  User:      {config['user']}")
    print(f"  Warehouse: {config['warehouse']}")
    print(f"  Database:  {config['database']}")
    print(f"  Schema:    {config['schema']}")
    print()

    try:
        conn = snowflake.connector.connect(
            user=config["user"],
            password=config["password"],
            account=config["account"],
            warehouse=config["warehouse"],
            database=config["database"],
            schema=config["schema"]
        )
        print("✅ SUCCESS: Connection established!")
        
        # Test a simple query
        cur = conn.cursor()
        cur.execute("SELECT current_version()")
        row = cur.fetchone()
        print(f"   Snowflake Version: {row[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILURE: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
