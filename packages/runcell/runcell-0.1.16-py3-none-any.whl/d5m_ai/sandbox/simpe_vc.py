from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado
import json
import asyncio
from .codet import create_custom_json_serializer
from .visualization import create_visualization_capture_functions

# Comparing with VirtualCellHandler, this have side effect of change the kernel state

class SimpleVirtualCellHandler(APIHandler):
    @tornado.web.authenticated
    async def post(self):
        input_data = self.get_json_body()
        code = input_data.get("code", "")

        kernel_id = input_data.get("kernel_id", None)
        if not kernel_id:
            self.set_status(400)
            self.finish(
                json.dumps({"success": False, "error": "No kernel_id provided"})
            )
            return
        
        km = self.kernel_manager
        if kernel_id not in km:
            self.set_status(404)
            self.finish(
                json.dumps({"success": False, "error": f"Kernel ID {kernel_id} not found"})
            )
            return
        
        kc = km.get_kernel(kernel_id).client()

        try:
            msg_id = kc.execute(code, store_history=False)
            
            # Wait for messages and collect all outputs
            outputs = []
            result_data = None
            
            # Keep track of execution state
            execution_complete = False
            shell_msg_received = False
            
            # Process messages until we get everything we need
            while (
                not (execution_complete and shell_msg_received) and len(outputs) < 20
            ):
                try:
                    msg = await kc.get_iopub_msg(timeout=2.0)
                    if (
                        msg["msg_type"] == "status"
                        and msg["content"]["execution_state"] == "idle"
                    ):
                        execution_complete = True
                    elif msg["msg_type"] == "stream":
                        outputs.append(msg["content"]["text"])
                    elif msg["msg_type"] == "execute_result":
                        result_data = msg["content"]["data"]
                        if "text/plain" in result_data:
                            serialized_simple = result_data["text/plain"].strip("'\"")
                            print(f"Found result text: {serialized_simple[:50]}...")
                    elif msg["msg_type"] == "error":
                        print(
                            f"Error in execution: {msg['content']['ename']}: {msg['content']['evalue']}"
                        )
                        traceback_str = "\n".join(msg["content"]["traceback"])
                        print(f"Traceback: {traceback_str}")
                        outputs.append(
                            f"ERROR: {msg['content']['ename']}: {msg['content']['evalue']}"
                        )
                except asyncio.TimeoutError:
                    print("Timeout waiting for output message")
                    if shell_msg_received and execution_complete:
                        break

                # Also check for the shell reply (execution status)
                if not shell_msg_received:
                    try:
                        shell_msg = await kc.get_shell_msg(timeout=0.1)
                        print(f"Shell message status: {shell_msg['content']['status']}")
                        shell_msg_received = True
                    except asyncio.TimeoutError:
                        pass

            print(f"All outputs: {outputs}")

            # Check if we have a result
            if result_data is None:
                self.set_status(500)
                self.finish(
                    json.dumps(
                        {
                            "success": False,
                            "error": "No result returned from virtual cell execution",
                        }
                    )
                )
                return
            else:
                # We have a direct result
                if "text/plain" in result_data:
                    serialized_simple = result_data["text/plain"].strip("'\"")
                    print(f"Found result text: {serialized_simple[:50]}...")
                    
                    # Safely evaluate the result    
                    import ast
                    result = ast.literal_eval(serialized_simple)
                    
                    # Send the response
                    self.finish(json.dumps({"success": True, "result": result}))
                else:
                    self.set_status(500)
                    self.finish(
                        json.dumps(
                            {
                                "success": False,
                                "error": "Result doesn't contain expected text/plain data",
                            }
                        )
                    )
        except Exception as e:
            # Handle any exceptions in our code
            import traceback
            traceback_str = traceback.format_exc()
     