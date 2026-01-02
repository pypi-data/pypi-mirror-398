import asyncio
import os
import subprocess
import shlex
import uuid


class ShellExecutor:
    def __init__(self):
        # Track working directory across commands. Note that plain `cd ...` in a
        # subprocess does not persist; we implement `cd` as a built-in below.
        self.cwd = os.getcwd()

        self.dangerous_patterns = [
            'rm -rf', 'rm -r', 'rmdir', 'del', 'format', 'fdisk',
            'mkfs', 'dd if=', 'dd of=', '> /dev/', 'shutdown', 'reboot',
            'halt', 'poweroff', 'init 0', 'init 6', 'kill -9', 'killall',
            'chmod 777', 'chmod -R 777', 'chown -R', 'passwd', 'su -',
            'sudo su', 'sudo rm', 'sudo chmod', 'sudo chown', '&&', '||',
            ';', '|', '>', '>>', '<', 'curl', 'wget', 'nc ', 'netcat',
            'python -c', 'python3 -c', 'eval', 'exec', 'import os',
            # Package managers / networked operations (require explicit permission)
            'pip install', 'pip uninstall', 'pip download',
            'conda install', 'conda update', 'conda remove',
            'npm install', 'npm i', 'npm add',
            'yarn add', 'yarn install',
            'pnpm add', 'pnpm install',
            # Git operations that modify state or reach network (require permission)
            'git checkout', 'git switch', 'git reset', 'git clean',
            'git pull', 'git push', 'git fetch',
        ]
        
        self.safe_commands = [
            'ls', 'dir', 'pwd', 'whoami', 'id', 'date', 'uptime', 'uname',
            'hostname', 'sw_vers',
            'df', 'du', 'free', 'ps', 'top', 'htop', 'which', 'where',
            'cat', 'head', 'tail', 'wc', 'grep', 'find', 'locate',
            'echo', 'env', 'printenv', 'history', 'file', 'stat',
            'tree', 'jq',
            'lsblk', 'lscpu', 'lsmem', 'lsusb', 'lspci',
            'ifconfig', 'ip', 'netstat', 'ss', 'ping', 'traceroute',
            # Git (read-only)
            'git status', 'git log', 'git branch', 'git diff', 'git show', 'git rev-parse', 'git --version',
            # Node/Python package tools (read-only)
            'npm list', 'npm ls', 'npm --version', 'npm -v',
            'pip list', 'pip show', 'pip check', 'pip --version', 'pip -v', 'pip -V',
            'conda list', 'conda info', 'conda --version',
            # Container / cluster inspection (read-only)
            'docker ps', 'docker images', 'docker --version', 'docker version',
            'kubectl get', 'kubectl version',
            # Jupyter tooling (explicitly allow nbconvert and kernelspec listing)
            'jupyter --version', 'jupyter nbconvert', 'jupyter kernelspec',
            # Convenience built-ins (cd is handled specially, but we still allow it)
            'cd',
        ]

    def _is_dangerous_command(self, command):
        """Check if a command contains dangerous patterns."""
        command_lower = command.lower().strip()
        
        for pattern in self.dangerous_patterns:
            if pattern in command_lower:
                return True, pattern
        return False, None

    def _is_safe_command(self, command):
        """Check if a command is in the safe commands list."""
        command_parts = shlex.split(command.lower())
        if not command_parts:
            return False, "Empty command"
            
        base_command = command_parts[0]
        
        # Allow a limited set of subcommands for multi-tool CLIs.
        if base_command in ['git', 'npm', 'pip', 'conda', 'docker', 'kubectl', 'jupyter']:
            if len(command_parts) < 2:
                return False, f"{base_command} requires a subcommand or flag"
            full_command = f"{base_command} {command_parts[1]}"
            allowed = {cmd for cmd in self.safe_commands if cmd.startswith(f"{base_command} ")}
            if full_command not in allowed:
                return False, f"{full_command} is not in the allowed commands list"
        elif base_command not in [cmd.split()[0] for cmd in self.safe_commands]:
            return False, f"Command '{base_command}' is not in the allowed commands list"
        
        return True, None

    async def request_permission(self, handler, command, dangerous_pattern):
        """Request user permission for dangerous commands."""
        request_id = str(uuid.uuid4())
        
        # Create a waiter for the permission response
        permission_waiter = asyncio.get_running_loop().create_future()
        
        # Store the waiter temporarily
        original_waiter = handler.waiter
        handler.waiter = permission_waiter
        
        try:
            # Send permission request to frontend
            await handler._safe_write_message({
                "type": "shell_permission_request",
                "command": command,
                "dangerous_pattern": dangerous_pattern,
                "request_id": request_id,
                "connection_id": handler.connection_id,
            })
            
            # Wait for user response (with timeout)
            try:
                permission_response = await asyncio.wait_for(permission_waiter, timeout=90.0)
                return permission_response and permission_response.get("allowed") == True
            except asyncio.TimeoutError:
                return False
        finally:
            # Restore original waiter
            handler.waiter = original_waiter

    async def execute_command(self, handler, command: str) -> str:
        """
        Execute shell commands directly on the server with security checks and user permission for dangerous commands.
        """
        # Safety check - identify potentially dangerous commands
        is_dangerous, dangerous_pattern = self._is_dangerous_command(command)

        # Built-in: support `cd` by updating the executor's working directory.
        try:
            parts = shlex.split(command)
        except Exception:
            parts = []
        if parts and parts[0].lower() == "cd":
            if len(parts) == 1:
                target = os.path.expanduser("~")
            else:
                target = os.path.expanduser(parts[1])
                if not os.path.isabs(target):
                    target = os.path.join(self.cwd, target)
            target = os.path.realpath(target)
            if not os.path.isdir(target):
                return f"Error: directory does not exist: {target}"
            self.cwd = target
            return f"Changed directory to: {self.cwd}"

        # If dangerous OR not allowlisted, ask for user confirmation.
        if is_dangerous:
            permission_granted = await self.request_permission(handler, command, dangerous_pattern)
            if not permission_granted:
                return f"Command execution cancelled by user. Command was: {command}"
        else:
            is_safe, error_msg = self._is_safe_command(command)
            if not is_safe:
                permission_granted = await self.request_permission(
                    handler,
                    command,
                    f"not_allowlisted: {error_msg}",
                )
                if not permission_granted:
                    return f"Command execution cancelled by user. Command was: {command}"
        
        try:
            print(f"[SHELL] Executing command: {command}")
            
            # Execute the command with timeout and capture output
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=90,  # 30 second timeout
                cwd=self.cwd  # Run in tracked working directory
            )
            
            # Combine stdout and stderr
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}"
            if result.stderr:
                if output:
                    output += f"\n\nSTDERR:\n{result.stderr}"
                else:
                    output += f"STDERR:\n{result.stderr}"
            
            if result.returncode != 0:
                output += f"\n\nReturn code: {result.returncode}"
            
            if not output.strip():
                output = "Command executed successfully (no output)"
            
            print(f"[SHELL] Command completed with return code: {result.returncode}")
            return output
            
        except subprocess.TimeoutExpired:
            print(f"[SHELL] Command timed out: {command}")
            return f"Error: Command timed out after 30 seconds"
        except subprocess.CalledProcessError as e:
            print(f"[SHELL] Command failed: {e}")
            return f"Error: Command failed with return code {e.returncode}\nSTDERR: {e.stderr}"
        except Exception as e:
            print(f"[SHELL] Unexpected error: {e}")
            return f"Error: Unexpected error occurred: {str(e)}" 