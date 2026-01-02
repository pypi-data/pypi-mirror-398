from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado
import json
import asyncio
import logging
from typing import Dict, Any
import uuid
from .codet import create_custom_json_serializer
from .visualization import create_visualization_capture_functions

logger = logging.getLogger(__name__)


class VirtualCellHandler(APIHandler):
    """Handler for forking kernel state and executing code in isolation."""
    
    # Constants
    MAX_OUTPUT_MESSAGES = 50
    MESSAGE_TIMEOUT = 5.0
    SHELL_TIMEOUT = 0.5
    
    @tornado.web.authenticated
    async def post(self):
        """Fork kernel state and execute code in isolation."""
        try:
            input_data = self.get_json_body()
            code = input_data.get("code", "").strip()
            kernel_id = input_data.get("kernel_id")
            
            # Validate input
            if not kernel_id:
                self.set_status(400)
                self.finish(json.dumps({
                    "success": False, 
                    "error": "No kernel_id provided"
                }))
                return
                
            if not code:
                self.set_status(400)
                self.finish(json.dumps({
                    "success": False,
                    "error": "No code provided"
                }))
                return
            
            # Get kernel
            kernel_client = self._get_kernel_client(kernel_id)
            if not kernel_client:
                self.set_status(404)
                self.finish(json.dumps({
                    "success": False,
                    "error": f"Kernel ID {kernel_id} not found"
                }))
                return
            
            # Execute the fork operation
            result = await self._fork_and_execute(kernel_client, code)
            
            if result.get("success"):
                self.finish(json.dumps(result))
            else:
                self.set_status(result.get("status_code", 500))
                self.finish(json.dumps({
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "traceback": result.get("traceback", "")
                }))
                
        except Exception as e:
            logger.exception("Error in kernel fork handler")
            self.set_status(500)
            self.finish(json.dumps({
                "success": False,
                "error": f"Handler exception: {str(e)}"
            }))
    
    def _get_kernel_client(self, kernel_id: str):
        """Get kernel client for the given kernel ID."""
        km = self.kernel_manager
        if kernel_id not in km:
            return None
        return km.get_kernel(kernel_id).client()
    
    async def _fork_and_execute(self, kc, code: str) -> Dict[str, Any]:
        """Fork kernel state and execute code."""
        try:
            # Step 1: Capture current kernel state
            state_result = await self._capture_kernel_state(kc)
            if not state_result.get("success"):
                return state_result
            
            serialized_state = state_result["data"]
            
            # Step 2: Execute code in isolated context with captured state
            return await self._execute_in_fork(kc, code, serialized_state)
            
        except Exception as e:
            logger.exception("Error in fork and execute")
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }
    
    async def _capture_kernel_state(self, kc) -> Dict[str, Any]:
        """Capture current kernel state."""
        capture_code = """
import dill
import base64
import sys
from IPython import get_ipython
import threading

try:
    # Get IPython instance
    ipython = get_ipython()
    if ipython is None:
        raise RuntimeError("IPython not available")
    
    # Create a snapshot of the namespace keys to avoid dictionary size change errors
    # Use list() to create a static copy of keys at this moment
    namespace_keys = list(ipython.user_ns.keys())
    
    # Define excluded variables
    excluded_vars = {
        'In', 'Out', 'get_ipython', 'exit', 'quit', 
        '_', '__', '___', '_i', '_ii', '_iii',
        '_i1', '_i2', '_i3', '_i4', '_i5', '_i6', '_i7', '_i8', '_i9',
        '_oh', '_dh', '__name__', '__doc__', '__package__',
        '__loader__', '__spec__', '__annotations__', '__builtins__',
        '__builtin__', '__file__', '_sh', 'help'
    }
    
    # Capture user namespace, excluding system variables
    user_vars = {}
    failed_vars = []
    
    for k in namespace_keys:
        # Skip if key starts with underscore or is in excluded list
        if k.startswith('_') or k in excluded_vars:
            continue
            
        try:
            # Try to get the value - it might have been deleted
            if k in ipython.user_ns:
                v = ipython.user_ns[k]
                
                # Skip modules and other non-serializable types
                if hasattr(v, '__module__') and hasattr(v, '__name__'):
                    # This is likely a module or function from a module
                    continue
                
                # Test if variable is serializable
                dill.dumps(v)
                user_vars[k] = v
            else:
                # Variable was deleted during iteration
                continue
                
        except KeyError:
            # Variable was deleted between getting keys and accessing it
            continue
        except Exception as e:
            failed_vars.append((k, str(e)))
    
    # Report failed variables if any
    if failed_vars:
        print(f"Warning: Could not serialize {len(failed_vars)} variables")
        for var_name, error in failed_vars[:5]:  # Show first 5 failures
            print(f"  - '{var_name}': {error}")
    
    # Serialize state
    serialized = base64.b64encode(dill.dumps(user_vars)).decode('utf-8')
    print(f"STATE_CAPTURED:{serialized}")
    print(f"Captured {len(user_vars)} variables successfully")
    
except Exception as e:
    import traceback
    print(f"STATE_CAPTURE_ERROR:{str(e)}")
    traceback.print_exc()
"""
        
        result = await self._execute_and_collect(kc, capture_code)
        
        # Parse capture result
        for output in result.get("outputs", []):
            if "STATE_CAPTURED:" in output:
                serialized_data = output.split("STATE_CAPTURED:", 1)[1].strip()
                return {"success": True, "data": serialized_data}
            elif "STATE_CAPTURE_ERROR:" in output:
                error_msg = output.split("STATE_CAPTURE_ERROR:", 1)[1].strip()
                return {"success": False, "error": f"Failed to capture state: {error_msg}"}
        
        return {"success": False, "error": "Failed to capture kernel state"}
    
    async def _execute_in_fork(self, kc, code: str, serialized_state: str) -> Dict[str, Any]:
        """Execute code in forked context."""
        fork_id = str(uuid.uuid4())[:8]
        
        # Escape the serialized state and code properly
        escaped_state = serialized_state.replace('\\', '\\\\').replace('"', '\\"')
        escaped_code = code.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        
        execution_code = f'''
import dill
import base64
import json
import traceback
import sys
from io import StringIO
import contextlib

# Fork identifier for debugging
_fork_id = "{fork_id}"

try:
    # Decode state - handle potential padding issues
    _serialized_state = """{escaped_state}"""
    
    # Ensure proper base64 padding
    missing_padding = len(_serialized_state) % 4
    if missing_padding:
        _serialized_state += '=' * (4 - missing_padding)
    
    try:
        _state_bytes = base64.b64decode(_serialized_state)
        _forked_vars = dill.loads(_state_bytes)
    except Exception as decode_error:
        print(f"FORK_ERROR:{fork_id}:{{json.dumps({{'type': 'DecodeError', 'message': f'Failed to decode state: {{str(decode_error)}}', 'traceback': traceback.format_exc()}})}}")
        raise
    
    # Validate code syntax
    _code = """{escaped_code}"""
    compile(_code, '<fork>', 'exec')
    
    # Import serialization helpers
    {create_custom_json_serializer()}
    {create_visualization_capture_functions()}
    
    # Setup result structure
    _result = {{
        'result': None,
        'stdout': '',
        'stderr': '',
        'error': None,
        'display_data': [],
        'images': {{}},
        'rich_display': []
    }}
    
    # Setup display capturing
    from IPython.display import display
    from IPython.core.formatters import format_display_data
    
    _captured_displays = []
    
    def capture_display(obj, **kwargs):
        try:
            format_dict, metadata = format_display_data(obj)
            _captured_displays.append(format_dict)
        except:
            pass
        return None
    
    # Configure matplotlib
    try:
        import matplotlib
        matplotlib.use('Agg', force=True)
        import matplotlib.pyplot as plt
        _original_show = plt.show
        plt.show = lambda *args, **kwargs: None
    except ImportError:
        _original_show = None
    
    # Execute code with output capture
    _stdout = StringIO()
    _stderr = StringIO()
    
    with contextlib.redirect_stdout(_stdout), contextlib.redirect_stderr(_stderr):
        try:
            # Create isolated namespace with common imports
            _fork_namespace = dict(_forked_vars)
            _fork_namespace['display'] = capture_display
            
            # Add common imports that might be needed
            import pandas as pd
            import numpy as np
            _fork_namespace['pd'] = pd
            _fork_namespace['np'] = np
            
            # Execute code
            exec(_code, {{'__builtins__': __builtins__}}, _fork_namespace)
            
            # Capture matplotlib figures
            _result['images'] = capture_all_visualizations()
            
            # Try to get result from last expression
            _lines = _code.strip().split('\\n')
            _last_line = _lines[-1].strip()
            
            if (_last_line and 
                not any(_last_line.startswith(kw) for kw in ['def ', 'class ', 'if ', 'for ', 'while ', 'with ', 'import ', 'from ']) and
                not _last_line.endswith(':') and
                '=' not in _last_line and
                not _last_line.startswith('print')):
                try:
                    _result['result'] = eval(_last_line, {{'__builtins__': __builtins__}}, _fork_namespace)
                except:
                    pass
            
            # Capture any remaining matplotlib figures
            try:
                import matplotlib.pyplot as plt
                if plt.get_fignums():
                    _result['images'].update(capture_matplotlib_figures())
            except:
                pass
                
        except Exception as e:
            _result['error'] = {{
                'type': type(e).__name__,
                'message': str(e),
                'traceback': traceback.format_exc()
            }}
        finally:
            # Restore matplotlib
            try:
                if _original_show:
                    plt.show = _original_show
            except:
                pass
    
    # Get output
    _result['stdout'] = _stdout.getvalue()
    _result['stderr'] = _stderr.getvalue()
    _result['rich_display'] = _captured_displays
    
    # Serialize result
    serialized_result = json.dumps(_result, default=custom_json_serializer)
    print(f"FORK_RESULT:{fork_id}:{{serialized_result}}")
    
except SyntaxError as e:
    error_data = {{
        'type': 'SyntaxError',
        'message': str(e),
        'line': e.lineno if hasattr(e, 'lineno') else None,
        'offset': e.offset if hasattr(e, 'offset') else None,
        'text': e.text if hasattr(e, 'text') else None
    }}
    print(f"FORK_SYNTAX_ERROR:{fork_id}:{{json.dumps(error_data)}}")
except Exception as e:
    error_data = {{
        'type': type(e).__name__,
        'message': str(e),
        'traceback': traceback.format_exc()
    }}
    print(f"FORK_ERROR:{fork_id}:{{json.dumps(error_data)}}")
'''
        
        result = await self._execute_and_collect(kc, execution_code)
        
        # Parse execution result
        for output in result.get("outputs", []):
            if f"FORK_RESULT:{fork_id}:" in output:
                result_json = output.split(f"FORK_RESULT:{fork_id}:", 1)[1].strip()
                try:
                    fork_result = json.loads(result_json)
                    return {"success": True, "result": fork_result}
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"Failed to parse fork result: {e}",
                        "status_code": 500
                    }
            elif f"FORK_SYNTAX_ERROR:{fork_id}:" in output:
                error_json = output.split(f"FORK_SYNTAX_ERROR:{fork_id}:", 1)[1].strip()
                try:
                    error_data = json.loads(error_json)
                    error_msg = f"SyntaxError"
                    if error_data.get('line'):
                        error_msg += f" at line {error_data['line']}"
                    if error_data.get('offset'):
                        error_msg += f", position {error_data['offset']}"
                    error_msg += f": {error_data['message']}"
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "traceback": error_data.get('text', ''),
                        "status_code": 400
                    }
                except:
                    return {
                        "success": False,
                        "error": "Syntax error in code",
                        "status_code": 400
                    }
            elif f"FORK_ERROR:{fork_id}:" in output:
                error_json = output.split(f"FORK_ERROR:{fork_id}:", 1)[1].strip()
                try:
                    error_data = json.loads(error_json)
                    return {
                        "success": False,
                        "error": f"{error_data['type']}: {error_data['message']}",
                        "traceback": error_data.get('traceback', ''),
                        "status_code": 500
                    }
                except:
                    return {
                        "success": False,
                        "error": "Execution error",
                        "status_code": 500
                    }
        
        # Check for kernel errors
        if result.get("error"):
            return {
                "success": False,
                "error": result["error"],
                "traceback": result.get("traceback", ""),
                "status_code": 500
            }
        
        return {
            "success": False,
            "error": "No result returned from fork execution",
            "status_code": 500
        }
    
    async def _execute_and_collect(self, kc, code: str) -> Dict[str, Any]:
        """Execute code and collect all outputs.

        IMPORTANT: Only processes messages that match our msg_id to avoid
        stealing messages from other kernel clients (e.g., JupyterLab's main client).
        """
        outputs = []
        error = None
        traceback_str = ""

        # Execute code
        msg_id = kc.execute(code, store_history=False)

        # Collect messages - only those matching our msg_id
        execution_complete = False
        shell_reply_received = False
        message_count = 0
        timeout_count = 0
        max_timeouts = 10  # Allow some timeouts for messages not meant for us

        while not (execution_complete and shell_reply_received) and message_count < self.MAX_OUTPUT_MESSAGES:
            # Get IOPub messages
            try:
                msg = await asyncio.wait_for(
                    kc.get_iopub_msg(),
                    timeout=self.MESSAGE_TIMEOUT
                )

                # Filter by msg_id - only process messages from our execution
                parent_msg_id = msg.get("parent_header", {}).get("msg_id")
                if parent_msg_id != msg_id:
                    # This message is not for us, skip it but don't count towards limit
                    continue

                message_count += 1
                timeout_count = 0  # Reset timeout count on successful message

                if msg["msg_type"] == "status" and msg["content"]["execution_state"] == "idle":
                    execution_complete = True
                elif msg["msg_type"] == "stream":
                    outputs.append(msg["content"]["text"])
                elif msg["msg_type"] == "error":
                    error = f"{msg['content']['ename']}: {msg['content']['evalue']}"
                    traceback_str = "\n".join(msg['content']['traceback'])
                elif msg["msg_type"] == "execute_result":
                    # Handle execute_result if needed
                    pass

            except asyncio.TimeoutError:
                timeout_count += 1
                if shell_reply_received and execution_complete:
                    break
                if timeout_count >= max_timeouts:
                    logger.warning(f"Too many timeouts waiting for IOPub message (count: {message_count})")
                    break

            # Get shell reply
            if not shell_reply_received:
                try:
                    shell_msg = await asyncio.wait_for(
                        kc.get_shell_msg(),
                        timeout=self.SHELL_TIMEOUT
                    )
                    # Filter shell messages by msg_id too
                    shell_parent_msg_id = shell_msg.get("parent_header", {}).get("msg_id")
                    if shell_parent_msg_id == msg_id:
                        shell_reply_received = True
                        if shell_msg["content"]["status"] == "error":
                            error = f"{shell_msg['content']['ename']}: {shell_msg['content']['evalue']}"
                            traceback_str = "\n".join(shell_msg['content']['traceback'])
                except asyncio.TimeoutError:
                    pass

        return {
            "outputs": outputs,
            "error": error,
            "traceback": traceback_str
        }


def setup_handlers(web_app):
    """Setup the kernel fork handler."""
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    
    route_pattern = url_path_join(base_url, "api", "d5m_ai", "virtualcell")
    handlers = [(route_pattern, VirtualCellHandler)]
    
    web_app.add_handlers(host_pattern, handlers)
    logger.info(f"Registered kernel fork handler at {route_pattern}")