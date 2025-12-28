#!/usr/bin/env python3
"""Test script to debug MCP server communication."""

import subprocess
import json
import sys
import time

def test_mcp_server():
    """Test the MCP server with proper initialization sequence."""
    
    # Start the MCP server process
    print("Starting MCP server...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/raj.hindocha/Work/pocs/mcp",
        env={
            "FASTAPI_URL": "http://localhost:8000",
            "PATH": "/usr/bin:/bin:/usr/local/bin"
        }
    )
    
    def send_request(request):
        """Send a JSON-RPC request and read response."""
        req_str = json.dumps(request) + "\n"
        print(f">>> Sending: {req_str.strip()}")
        proc.stdin.write(req_str)
        proc.stdin.flush()
        
        # Read response
        try:
            response = proc.stdout.readline()
            print(f"<<< Received: {response.strip()}")
            return json.loads(response) if response else None
        except Exception as e:
            print(f"!!! Error reading response: {e}")
            return None
    
    try:
        # Step 1: Initialize
        print("\n=== Step 1: Initialize ===")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        }
        init_response = send_request(init_request)
        
        # Step 2: Send initialized notification
        print("\n=== Step 2: Initialized notification ===")
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        proc.stdin.write(json.dumps(initialized_notification) + "\n")
        proc.stdin.flush()
        print(f">>> Sent initialized notification")
        time.sleep(0.5)
        
        # Step 3: List tools
        print("\n=== Step 3: List tools ===")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        tools_response = send_request(list_tools_request)
        
        # Step 4: Call list_datasources
        print("\n=== Step 4: Call list_datasources ===")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_datasources",
                "arguments": {}
            }
        }
        result = send_request(call_request)
        
        print("\n=== Final Result ===")
        print(json.dumps(result, indent=2) if result else "No response")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Read any stderr
        proc.stdin.close()
        stderr_output = proc.stderr.read()
        if stderr_output:
            print(f"\n=== STDERR ===\n{stderr_output}")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_mcp_server()
