#!/usr/bin/env python3
"""
PowerShell 7 Command Executor Wrapper
Executes PowerShell 7 commands directly, bypassing cmd.exe constraints
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, Any


class PS7Executor:
    def __init__(self):
        self.ps7_path = "pwsh"
    
    def execute(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Execute PowerShell 7 command
        
        Args:
            command: PowerShell command to execute
            timeout: Command timeout in seconds (default 60)
        
        Returns:
            Dict with exit_code, stdout, stderr, and success status
        """
        try:
            result = subprocess.run(
                [self.ps7_path, "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timeout after {timeout} seconds",
                "command": command
            }
        
        except FileNotFoundError:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "PowerShell 7 (pwsh) not found in PATH",
                "command": command
            }
        
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "command": command
            }


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No command provided",
            "usage": "python ps7_executor.py <powershell-command>"
        }), file=sys.stderr)
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    executor = PS7Executor()
    result = executor.execute(command)
    
    print(json.dumps(result, indent=2))
    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
