import dill
from concurrent.futures import ProcessPoolExecutor
from IPython import get_ipython
from textwrap import dedent

executor = ProcessPoolExecutor()


def extract_imports_from_history():
    """Extract import statements from cell execution history"""
    ip = get_ipython()
    imports = []

    # Get cell history
    history = ip.history_manager.get_range()

    for _, _, cell in history:
        # Parse cell for import statements
        import ast

        try:
            tree = ast.parse(cell)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(ast.unparse(node))
        except:
            pass

    return imports


def get_user_imports():
    """Capture all imports from user namespace"""
    ip = get_ipython()
    modules = {}

    for name, obj in ip.user_ns.items():
        if (
            not name.startswith("_")
            and isinstance(obj, type(sys))
            and hasattr(obj, "__file__")
        ):
            try:
                import_stmt = f"import {obj.__name__}"
                if obj.__name__ != name:
                    import_stmt += f" as {name}"
                modules[name] = import_stmt
            except:
                pass

    return modules


def optimize_large_objects(user_vars):
    """Use shared memory for large numpy/pandas objects"""
    import numpy as np
    import tempfile
    import os

    optimized_vars = {}
    temp_files = []

    for k, v in user_vars.items():
        if isinstance(v, np.ndarray) and v.nbytes > 10_000_000:  # 10MB threshold
            # Create memmap file
            fd, filename = tempfile.mkstemp(suffix=".npy")
            np.save(filename, v)
            temp_files.append(filename)

            # Replace with reference
            optimized_vars[k] = {
                "type": "numpy.memmap",
                "filename": filename,
                "shape": v.shape,
                "dtype": str(v.dtype),
            }
        else:
            optimized_vars[k] = v

    return optimized_vars, temp_files


# And in the child process:
def reconstruct_large_objects(vars_dict):
    import numpy as np

    for k, v in vars_dict.items():
        if isinstance(v, dict) and "type" in v and v["type"] == "numpy.memmap":
            vars_dict[k] = np.load(v["filename"], mmap_mode="r")

    return vars_dict


def execute_virtual_cell(code: str, user_vars: dict, imports: list):
    import sys
    from io import StringIO
    from traceback import format_exc

    # 重定向输出
    sys.stdout = stdout_catcher = StringIO()
    sys.stderr = stderr_catcher = StringIO()
    result = None

    try:
        # Set up environment with imports first
        setup_code = "\n".join(imports)
        exec(setup_code, env)
        # 创建隔离环境（深拷贝原始变量）
        env = dict(user_vars)
        env["__builtins__"] = __builtins__

        # 执行代码并捕获最后表达式
        exec(
            dedent(
                f"""
            _virtualcell_result = None
            {code}
            if '_virtualcell_result' in locals():
                _virtualcell_result = locals()['_virtualcell_result']
            else:
                try:
                    _virtualcell_result = eval(code.splitlines()[-1])
                except:
                    pass
        """
            ),
            env,
        )

        result = env.get("_virtualcell_result")

    except Exception as e:
        error_trace = format_exc()
        line_info = None

        # Extract line information from traceback
        import re

        match = re.search(r"line (\d+)", error_trace)
        if match:
            line_num = int(match.group(1))
            lines = code.split("\n")
            start = max(0, line_num - 2)
            end = min(len(lines), line_num + 1)
            context_lines = lines[start:end]
            line_info = {"line_number": line_num, "context": context_lines}

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_trace,
            "line_info": line_info,
            "stdout": stdout_catcher.getvalue(),
            "stderr": stderr_catcher.getvalue(),
        }

    return {
        "success": True,
        "result": dill.dumps(result),
        "stdout": stdout_catcher.getvalue(),
        "stderr": stderr_catcher.getvalue(),
    }


async def virtualcell_handler(code: str):
    """处理前端请求"""
    ip = get_ipython()
    user_ns = {k: v for k, v in ip.user_ns.items() if not k.startswith("_")}

    # 深度序列化变量
    serialized_vars = dill.dumps(user_ns)

    # 提交子进程任务
    future = executor.submit(
        execute_virtual_cell, code=code, user_vars=dill.loads(serialized_vars)
    )

    return await future
