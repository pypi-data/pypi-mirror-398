"""
CLI entry point for AI Project OS MCP Server.
"""

import argparse
import sys
import os
from ai_project_os_mcp.server import MCPServer
from ai_project_os_mcp.config import config

def main():
    parser = argparse.ArgumentParser(description="AI Project OS MCP Server")
    parser.add_argument("--start", action="store_true", help="Start the MCP server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio", help="Transport mode (stdio or http)")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP server")
    parser.add_argument("--root", default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    if args.start:
        # Update config with CLI args
        config.project_root = args.root
        
        server = MCPServer(project_root=args.root)
        
        print(f"Starting MCP Server ({args.transport})...")
        print(f"Project Root: {os.path.abspath(args.root)}")
        
        if args.transport == "stdio":
            server.start_stdio()
        elif args.transport == "http":
            server.start_http(port=args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
