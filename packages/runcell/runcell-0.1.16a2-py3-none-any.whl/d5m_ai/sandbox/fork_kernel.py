
import tornado
from tornado.web import authenticated
import tempfile
from jupyter_server.base.handlers import APIHandler
import json
import base64
import asyncio
import os


class ForkKernelHandler(APIHandler):
    """Handler for forking a kernel with its session state using dill."""

    @authenticated
    async def post(self):
        try:
            # Parse the request body
            body = self.get_json_body()
            kernel_id = body.get("kernel_id")
            notebook_path = body.get("notebook_path")
            active_cell_index = body.get("active_cell_index")
            timeout = body.get('timeout', 2.0)  # Default to 2.0 if not provided

            print(f"Received request to fork kernel {kernel_id}")  # Debug log

            if not kernel_id:
                self.set_status(400)
                self.finish(json.dumps({"error": "Missing kernel_id parameter"}))
                return

            # Get the kernel from the kernel manager
            kernel_manager = self.kernel_manager
            if kernel_id not in kernel_manager.list_kernel_ids():
                print(f"Kernel {kernel_id} not found")  # Debug log
                self.set_status(404)
                self.finish(json.dumps({"error": f"Kernel {kernel_id} not found"}))
                return

            # Create a temporary file to store the session state
            with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as temp_file:
                session_file_path = temp_file.name

            try:
                # Debug: Check source kernel state
                source_kernel = kernel_manager.get_kernel(kernel_id)
                source_kernel_client = source_kernel.client()
                
                # Execute code to check source kernel state
                check_state_code = """
import sys
print("Source kernel state:")
print(f"Variables in namespace: {list(globals().keys())}")
print(f"Loaded modules: {list(sys.modules.keys())}")
"""
                msg_id = source_kernel_client.execute(check_state_code, silent=False)
                
                # Wait for execution to complete
                while True:
                    try:
                        msg = await source_kernel_client.get_iopub_msg(timeout=2.0)
                        if msg["msg_type"] == "stream":
                            print(f"Source kernel output: {msg['content']['text']}")
                        elif msg["msg_type"] == "status" and msg["content"]["execution_state"] == "idle":
                            break
                    except asyncio.TimeoutError:
                        break

                # Create new kernel and check its state
                new_kernel_id = await self.kernel_manager.start_kernel(
                    kernel_name=source_kernel.kernel_name
                )
                new_kernel = self.kernel_manager.get_kernel(new_kernel_id)
                new_kernel_client = new_kernel.client()

                # Check new kernel state before loading session
                check_new_state_code = """
import sys
print("New kernel state before loading:")
print(f"Variables in namespace: {list(globals().keys())}")
print(f"Loaded modules: {list(sys.modules.keys())}")
"""
                msg_id = new_kernel_client.execute(check_new_state_code, silent=False)
                
                # Wait for execution to complete
                while True:
                    try:
                        msg = await new_kernel_client.get_iopub_msg(timeout=timeout)
                        if msg["msg_type"] == "stream":
                            print(f"New kernel output: {msg['content']['text']}")
                        elif msg["msg_type"] == "status" and msg["content"]["execution_state"] == "idle":
                            break
                    except asyncio.TimeoutError:
                        break

                # Modify the dump code to save actual kernel state
                dump_code = f"""
import dill
import os
import sys
import pickle
from IPython import get_ipython

# Define the path for the session state
session_file_path = '{session_file_path}'

# Get the IPython instance
ip = get_ipython()
if ip is not None:
    # Get all variables from the user namespace
    user_ns = ip.user_ns.copy()
    
    # Remove IPython's internal variables
    for key in list(user_ns.keys()):
        if key.startswith('_') or key in ['exit', 'quit', 'get_ipython']:
            del user_ns[key]
    
    print(f"Initial variables: {{list(user_ns.keys())}}")
    
    # Test each variable to see if it can be pickled
    safe_vars = {{}}
    problem_vars = []
    
    for key, value in user_ns.items():
        try:
            # Test if the object can be pickled
            pickle.dumps(value)
            safe_vars[key] = value
        except Exception as e:
            problem_vars.append((key, str(type(value)), str(e)))
    
    print(f"Safe variables being saved: {{list(safe_vars.keys())}}")
    if problem_vars:
        print(f"Skipping non-serializable variables: {{[v[0] for v in problem_vars]}}")
        for var, typ, err in problem_vars:
            print(f"  - {{var}} ({{typ}}): {{err}}")
    
    try:
        # Save the filtered state with protocol 4 for compatibility
        with open(session_file_path, 'wb') as f:
            dill.dump(safe_vars, f, protocol=4)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        print(f"Saved kernel state to {{session_file_path}}")
        print(f"File size: {{os.path.getsize(session_file_path)}} bytes")
        
        # Verify the file is valid
        with open(session_file_path, 'rb') as f:
            test_load = dill.load(f)
            print(f"Verified file can be loaded, contains {{len(test_load)}} variables")
    except Exception as e:
        print(f"Error during serialization: {{str(e)}}")
        raise
"""
                # Execute code to dump session on the source kernel
                msg_id = source_kernel_client.execute(dump_code, silent=False)
                
                # Wait for execution to complete with better error handling
                execution_complete = False
                dump_error = None
                while not execution_complete:
                    try:
                        msg = await source_kernel_client.get_iopub_msg(timeout=5.0)
                        if msg["msg_type"] == "stream":
                            print(f"Dump output: {msg['content']['text']}")
                        elif msg["msg_type"] == "error":
                            dump_error = f"{msg['content']['ename']}: {msg['content']['evalue']}"
                            print(f"Dump error: {dump_error}")
                            break
                        elif msg["msg_type"] == "status" and msg["content"]["execution_state"] == "idle":
                            execution_complete = True
                    except asyncio.TimeoutError:
                        # Check if kernel is still alive
                        if not source_kernel.is_alive():
                            dump_error = "Source kernel died during serialization"
                            break
                        if execution_complete:
                            break
                        continue

                if dump_error:
                    raise Exception(f"Failed to serialize kernel state: {dump_error}")

                # Verify the file exists and has content before proceeding
                if not os.path.exists(session_file_path) or os.path.getsize(session_file_path) == 0:
                    raise Exception("Session file was not created or is empty")

                # Read and encode the session file
                with open(session_file_path, "rb") as f:
                    session_data = f.read()
                
                if len(session_data) == 0:
                    raise Exception("Session data is empty after reading file")
                    
                print(f"Read {len(session_data)} bytes from session file")
                session_b64 = base64.b64encode(session_data).decode("utf-8")

                # Modify the bootstrap code to test loading the simple state
                bootstrap_code = f"""
import base64
import dill
import tempfile
import os
import sys
import traceback
from IPython import get_ipython

try:
    # Decode the session data from base64
    session_data = base64.b64decode('{session_b64}')
    print(f"Decoded session data size: {{len(session_data)}} bytes")
    
    if len(session_data) == 0:
        raise Exception("Decoded session data is empty")

    # Create a temporary file to store the session data
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as temp_file:
        temp_file.write(session_data)
        temp_file.flush()
        os.fsync(temp_file.fileno())  # Ensure data is written to disk
        temp_session_path = temp_file.name
    print(f"Created temporary file at: {{temp_session_path}}")
    print(f"Temporary file size: {{os.path.getsize(temp_session_path)}} bytes")

    # Load the state with better error handling
    with open(temp_session_path, 'rb') as f:
        print("Attempting to load state...")
        try:
            state = dill.load(f)
            print(f"State loaded successfully with {{len(state)}} variables")
            print(f"Variables loaded: {{list(state.keys())}}")
        except EOFError:
            f.seek(0)
            content = f.read()
            print(f"EOFError encountered. File size: {{len(content)}} bytes, content starts with: {{content[:100] if content else 'empty'}}")
            raise
        except Exception as load_error:
            print(f"Error loading state: {{str(load_error)}}")
            f.seek(0)
            content = f.read()
            print(f"File content length: {{len(content)}} bytes")
            raise

    # Clean up
    os.unlink(temp_session_path)
    print("Temporary file cleaned up")

    # Restore the state
    ip = get_ipython()
    if ip is not None:
        print("Restoring state...")
        # Update the IPython namespace with test state
        ip.user_ns.update(state)
        
        # Force a namespace refresh
        ip.run_cell('import sys; sys.modules[__name__].__dict__.update(globals())')
        
        # Clear any existing output
        ip.displayhook.flush()
        print("State restored successfully")

    print("Session state successfully loaded from source notebook.")

except Exception as error:
    error_msg = f"Error loading session: {{str(error)}}\\n{{traceback.format_exc()}}"
    print(error_msg)
    raise Exception(error_msg)
"""
                # Execute bootstrap code on the new kernel
                msg_id = new_kernel_client.execute(bootstrap_code, silent=True)
                
                # Wait for execution to complete and check for any errors
                execution_complete = False
                execution_error = None
                while not execution_complete:
                    try:
                        msg = await new_kernel_client.get_iopub_msg(timeout=timeout)
                        if msg["msg_type"] == "status" and msg["content"]["execution_state"] == "idle":
                            execution_complete = True
                        elif msg["msg_type"] == "error":
                            execution_error = f"{msg['content']['ename']}: {msg['content']['evalue']}"
                            break
                    except asyncio.TimeoutError:
                        # If we timeout, check if the kernel is still alive
                        if not new_kernel.is_alive():
                            execution_error = "Kernel died during execution"
                            break
                        # If kernel is alive but we got no message, continue waiting
                        continue
                    except Exception as msg_error:  # Changed variable name to avoid conflict
                        execution_error = f"Error waiting for kernel message: {str(msg_error)}"
                        break

                if execution_error:
                    raise Exception(f"Failed to load session state: {execution_error}")

                # After loading session, check new kernel state again
                check_final_state_code = """
import sys
print("New kernel state after loading:")
print(f"Variables in namespace: {list(globals().keys())}")
print(f"Loaded modules: {list(sys.modules.keys())}")
"""
                msg_id = new_kernel_client.execute(check_final_state_code, silent=False)
                
                # Wait for execution to complete
                while True:
                    try:
                        msg = await new_kernel_client.get_iopub_msg(timeout=2.0)
                        if msg["msg_type"] == "stream":
                            print(f"Final kernel output: {msg['content']['text']}")
                        elif msg["msg_type"] == "status" and msg["content"]["execution_state"] == "idle":
                            break
                    except asyncio.TimeoutError:
                        break

                # Return the new kernel info
                self.set_status(201)
                self.finish(
                    json.dumps(
                        {
                            "kernel_id": new_kernel_id,
                            "notebook_path": notebook_path,
                            "active_cell_index": active_cell_index,
                            "status": "success"
                        }
                    )
                )

            except Exception as e:
                print(f"Error in ForkKernelHandler: {str(e)}")  # Debug log
                print(f"Error type: {type(e)}")  # Debug log
                import traceback
                print(f"Traceback: {traceback.format_exc()}")  # Debug log
                self.log.error(f"Error while forking kernel: {str(e)}")
                self.set_status(500)
                self.finish(json.dumps({"error": str(e)}))
            finally:
                # Clean up the temporary file
                if os.path.exists(session_file_path):
                    os.unlink(session_file_path)

        except Exception as e:
            print(f"Error in ForkKernelHandler: {str(e)}")  # Debug log
            print(f"Error type: {type(e)}")  # Debug log
            import traceback
            print(f"Traceback: {traceback.format_exc()}")  # Debug log
            self.log.error(f"Error while forking kernel: {str(e)}")
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))
