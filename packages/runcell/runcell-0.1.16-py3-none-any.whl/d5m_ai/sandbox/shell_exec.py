from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado
import json
import asyncio
import subprocess
from .codet import create_custom_json_serializer
from .visualization import create_visualization_capture_functions

# Comparing with VirtualCellHandler, this have side effect of change the kernel state

class ShellExecHandler(APIHandler):
    @tornado.web.authenticated
    async def post(self):
        input_data = self.get_json_body()
        command = input_data.get("command", "")
        if not command:
            self.set_status(400)
            self.finish(json.dumps({"success": False, "error": "No command provided"}))
            return
        
        try:
            # Execute the shell command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            response = {
                "success": True,
                "command": command,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "returncode": process.returncode
            }
            
            self.finish(json.dumps(response, default=create_custom_json_serializer()))
            
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "success": False,
                "error": str(e),
                "command": command
            }))
        
        