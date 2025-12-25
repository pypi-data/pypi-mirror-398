"""
MCPServer - MCP Server Implementation
"""

import sys
import json
import asyncio
from ai_project_os_mcp.core.state_manager import StateManager
from ai_project_os_mcp.core.rule_engine import RuleEngine
from ai_project_os_mcp.config import config

class MCPServer:
    """
    MCP Server implementation for managing AI Project OS MCP rules and tools.
    Supports Stdio and HTTP transports.
    """
    
    def __init__(self, project_root="."):
        """
        Initialize MCP Server
        
        Args:
            project_root: Project root directory path
        """
        self.project_root = project_root
        self.state_manager = StateManager(project_root)
        self.rule_engine = RuleEngine()
        self.tools = {}
        
        # Register default tools
        from ai_project_os_mcp.tools import get_stage, freeze_stage, guard_src, submit_audit
        from ai_project_os_mcp.tools.context_tools import read_architecture, analyze_dependencies
        from ai_project_os_mcp.tools.verification_tools import run_tests, verify_audit_integrity
        from ai_project_os_mcp.tools.export_audit import export_audit
        from ai_project_os_mcp.tools.dashboard_tools import get_stats, cli_dashboard
        
        self.register_tool(get_stage)
        self.register_tool(freeze_stage)
        self.register_tool(guard_src)
        self.register_tool(submit_audit)
        self.register_tool(read_architecture)
        self.register_tool(analyze_dependencies)
        self.register_tool(run_tests)
        self.register_tool(verify_audit_integrity)
        self.register_tool(export_audit)
        self.register_tool(get_stats)
        self.register_tool(cli_dashboard)
    
    def register_tool(self, tool_func, tool_name=None):
        """
        Register an MCP tool
        
        Args:
            tool_func: Tool function
            tool_name: Tool name (optional, defaults to function name)
        """
        name = tool_name or tool_func.__name__
        self.tools[name] = tool_func
    
    def unregister_tool(self, tool_name):
        """
        Unregister an MCP tool
        
        Args:
            tool_name: Tool name
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
    
    def get_registered_tools(self):
        """
        Get list of registered tools
        
        Returns:
            list: List of registered tool names
        """
        return list(self.tools.keys())
    
    def handle_request(self, tool_name, payload=None):
        """
        Handle MCP tool request
        
        Args:
            tool_name: Tool name
            payload: Tool payload (optional)
            
        Returns:
            dict: Tool execution result
        """
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            # MCP Iron Rule: Must load state before any action
            state = self.state_manager.load_state()
            
            # Call tool
            result = self.tools[tool_name](state, payload or {})
            
            # If freeze_stage tool, update state
            if tool_name == "freeze_stage" and result.get("success"):
                self.state_manager.save_state(result["new_state"])
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def start_stdio(self):
        """
        Start server in Stdio mode (JSON-RPC style)
        """
        # Simple line-based JSON handler for now
        # In a real MCP implementation, this would handle JSON-RPC 2.0
        sys.stderr.write(f"MCP Server started (Stdio) at {self.project_root}\n")
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                tool_name = request.get("tool")
                payload = request.get("payload", {})
                req_id = request.get("id")
                
                result = self.handle_request(tool_name, payload)
                
                response = {
                    "id": req_id,
                    "result": result
                }
                
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                sys.stderr.write("Invalid JSON input\n")
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")

    def start_http(self, host="0.0.0.0", port=8000):
        """
        Start server in HTTP mode using FastAPI
        """
        try:
            import uvicorn
            from fastapi import FastAPI, HTTPException
            from pydantic import BaseModel
        except ImportError:
            print("Error: FastAPI and uvicorn are required for HTTP mode.")
            print("Pip install fastapi uvicorn")
            return

        app = FastAPI(title="AI Project OS MCP Server")
        
        class ToolRequest(BaseModel):
            tool: str
            payload: dict = {}

        @app.post("/mcp")
        async def handle_mcp_request(request: ToolRequest):
            result = self.handle_request(request.tool, request.payload)
            return result

        @app.get("/tools")
        async def list_tools():
            return {"tools": self.get_registered_tools()}
        
        @app.get("/api/stats")
        async def get_stats():
            """
            获取项目统计信息
            """
            # 加载当前状态
            state = self.state_manager.load_state()
            
            # 统计审计记录数量
            import os
            import re
            audit_count = 0
            audit_file = os.path.join(self.project_root, "docs", "S5_audit.md")
            if os.path.exists(audit_file):
                with open(audit_file, "r", encoding="utf-8") as f:
                    content = f.read()
                audit_count = len(re.findall(r"## Sub-task:", content))
            
            # 分析依赖情况
            dependencies_result = self.handle_request("analyze_dependencies", {})
            dependency_violations = len(dependencies_result.get("violations", []))
            
            # 构建统计信息
            stats = {
                "stage": state.get("stage", "unknown"),
                "version": state.get("version", "unknown"),
                "last_updated": state.get("last_updated", "unknown"),
                "audit_count": audit_count,
                "dependency_violations": dependency_violations,
                "registered_tools": len(self.tools),
                "project_root": self.project_root
            }
            
            return stats

        print(f"Starting MCP Server (HTTP) at http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)

    def validate_state(self):
        """
        Validate if current state conforms to MCP rules
        
        Returns:
            tuple: (is_valid, reason)
        """
        state = self.state_manager.load_state()
        
        # Validate stage
        if state["stage"] not in ["S1", "S2", "S3", "S4", "S5"]:
            return False, f"Invalid stage: {state['stage']}"
        
        # Validate version
        if "version" not in state:
            return False, "Missing version field"
        
        # Validate last_updated
        if "last_updated" not in state:
            return False, "Missing last_updated field"
        
        return True, "State is valid"
