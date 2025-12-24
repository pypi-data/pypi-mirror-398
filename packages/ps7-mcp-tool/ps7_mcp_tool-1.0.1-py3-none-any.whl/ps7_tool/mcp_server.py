#!/usr/bin/env python3
"""
PowerShell 7 MCP Server for Zencoder
Implements Model Context Protocol (MCP) for PowerShell command execution
Supports stdio communication for local MCP connections
"""

import json
import logging
import sys
import subprocess
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

log_dir = Path.home() / ".ps7_tool"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "mcp_server.log")
    ]
)
logger = logging.getLogger("PS7MCP")


class PS7MCPServer:
    def __init__(self):
        self.ps7_path = "pwsh"
        self.log_dir = Path.home() / ".ps7_tool" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.version = "1.0.0"
        self.request_id = 0
        logger.info("PS7 MCP Server initialized")
        
    def execute_command(
        self, 
        command: str, 
        timeout: int = 240,
        background: bool = False,
        cwd: Optional[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """Execute PowerShell command"""
        start_time = time.time()
        log_file = self._get_log_file()
        
        try:
            if background:
                return self._execute_background(command, cwd, log_file, description)
            else:
                return self._execute_foreground(command, timeout, cwd, log_file, description, start_time)
                
        except Exception as e:
            return self._error_response(str(e), log_file, start_time)
    
    def _execute_foreground(self, command: str, timeout: int, cwd: Optional[str], log_file: Path, description: str, start_time: float) -> Dict[str, Any]:
        """Execute command in foreground"""
        try:
            result = subprocess.run(
                [self.ps7_path, "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or None
            )
            
            execution_time = time.time() - start_time
            
            output = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time,
                "log_file": str(log_file)
            }
            
            self._write_log(log_file, {
                "command": command,
                "description": description,
                **output
            })
            return output
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            output = {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timeout after {timeout} seconds",
                "execution_time": execution_time,
                "log_file": str(log_file)
            }
            self._write_log(log_file, {
                "command": command,
                "description": description,
                **output
            })
            return output
            
        except FileNotFoundError:
            execution_time = time.time() - start_time
            output = {
                "exit_code": -1,
                "stdout": "",
                "stderr": "PowerShell 7 (pwsh) not found in PATH. Install from: https://github.com/PowerShell/PowerShell",
                "execution_time": execution_time,
                "log_file": str(log_file)
            }
            self._write_log(log_file, {
                "command": command,
                "description": description,
                **output
            })
            return output
    
    def _execute_background(self, command: str, cwd: Optional[str], log_file: Path, description: str) -> Dict[str, Any]:
        """Execute command in background"""
        try:
            process = subprocess.Popen(
                [self.ps7_path, "-NoProfile", "-Command", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd or None
            )
            
            output = {
                "exit_code": None,
                "stdout": f"Process started with PID {process.pid}",
                "stderr": "",
                "execution_time": 0,
                "log_file": str(log_file),
                "background": True,
                "pid": process.pid
            }
            
            self._write_log(log_file, {
                "command": command,
                "description": description,
                **output
            })
            return output
            
        except Exception as e:
            return self._error_response(str(e), log_file, time.time())
    
    def _error_response(self, error_msg: str, log_file: Path, start_time: float) -> Dict[str, Any]:
        """Generate error response"""
        execution_time = time.time() - start_time
        output = {
            "exit_code": -1,
            "stdout": "",
            "stderr": error_msg,
            "execution_time": execution_time,
            "log_file": str(log_file)
        }
        self._write_log(log_file, output)
        return output
    
    def _get_log_file(self) -> Path:
        """Generate log file path with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return self.log_dir / f"ps7_exec_{timestamp}.json"
    
    def _write_log(self, log_file: Path, output: dict):
        """Write command output to log file"""
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write log file {log_file}: {e}")


class MCPProtocol:
    """Implements MCP JSONRpc protocol"""
    
    def __init__(self, ps7_server: PS7MCPServer):
        self.ps7_server = ps7_server
        self.request_counter = 0
        logger.info("MCP Protocol handler initialized")
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP JSONRpc request"""
        self.request_counter += 1
        request_id = request.get("id", self.request_counter)
        method = request.get("method", "")
        params = request.get("params", {})
        
        logger.info(f"Received MCP request: {method}")
        
        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "tools/list":
                result = self._handle_tools_list()
            elif method == "tools/call":
                result = self._handle_tools_call(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Error handling {method}: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    def _handle_initialize(self, params: Dict) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "PS7 Tool",
                "version": "1.0.0"
            }
        }
    
    def _handle_tools_list(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            "tools": [
                {
                    "name": "execute_powershell",
                    "description": "Execute PowerShell 7 commands with support for timeout and background execution",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "PowerShell command to execute (e.g., 'Get-ChildItem', 'dir', 'mkdir')"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Timeout in seconds (default: 240)",
                                "default": 240
                            },
                            "background": {
                                "type": "boolean",
                                "description": "Run in background mode (returns immediately)",
                                "default": False
                            },
                            "cwd": {
                                "type": "string",
                                "description": "Working directory for command execution"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional description for logging"
                            }
                        },
                        "required": ["command"]
                    }
                }
            ]
        }
    
    def _handle_tools_call(self, params: Dict) -> Dict[str, Any]:
        """Handle tool call"""
        tool_name = params.get("name", "")
        tool_input = params.get("arguments", {})
        
        if tool_name != "execute_powershell":
            raise ValueError(f"Unknown tool: {tool_name}")
        
        command = tool_input.get("command", "")
        timeout = tool_input.get("timeout", 240)
        background = tool_input.get("background", False)
        cwd = tool_input.get("cwd")
        description = tool_input.get("description", "")
        
        if not command:
            raise ValueError("command parameter is required")
        
        result = self.ps7_server.execute_command(command, timeout, background, cwd, description)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }


def main():
    """Main MCP server loop"""
    ps7_server = PS7MCPServer()
    mcp_protocol = MCPProtocol(ps7_server)
    
    logger.info("Starting PS7 MCP Server")
    
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line)
                response = mcp_protocol.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
    
    except KeyboardInterrupt:
        logger.info("PS7 MCP Server shutting down")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
