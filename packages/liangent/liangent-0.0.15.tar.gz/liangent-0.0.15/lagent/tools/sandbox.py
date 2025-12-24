import ast
import multiprocessing
import sys
import time
import io
import contextlib
from typing import Any, Dict, List, Optional, Union

# === Security Configuration ===
ALLOWED_MODULES = {
    "math", "datetime", "json", "random", "re", 
    "collections", "itertools", "functools", "statistics"
}

# Blacklisted built-in functions
BLACKLISTED_BUILTINS = {
    "open", "exec", "eval", "compile", "input", 
    "globals", "locals", "exit", "quit", "help"
}

class SecurityViolation(Exception):
    pass

class ExecutionTimeout(Exception):
    pass

class ASTValidator(ast.NodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split('.')[0] not in ALLOWED_MODULES:
                self.errors.append(f"Importing module '{alias.name}' is not allowed.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split('.')[0] not in ALLOWED_MODULES:
             self.errors.append(f"Importing from module '{node.module}' is not allowed.")
        self.generic_visit(node)
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in BLACKLISTED_BUILTINS:
                self.errors.append(f"Function '{node.func.id}' is blocked.")
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        # Prevent accessing some dangerous attributes directly if possible
        # This is hard to perfect safely with AST-only, but we catch __ stuff
        if node.attr.startswith("__"):
             self.errors.append(f"Accessing private/magic attribute '{node.attr}' is restricted.")
        self.generic_visit(node)

    def validate(self, code: str):
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SecurityViolation(f"Syntax Error: {e}")
        
        self.visit(tree)
        if self.errors:
            raise SecurityViolation("\n".join(self.errors))

def _safe_exec(code: str, return_dict, timeout: int):
    # Redirect stdout/stderr to capture output
    output_buffer = io.StringIO()
    
    # Secure environment: remove dangerous globals
    safe_globals = {"__builtins__": {}}
    
    # Restore safe builtins
    import builtins
    for name in dir(builtins):
        if name == "__import__":
             safe_globals["__builtins__"][name] = getattr(builtins, name)
             continue
             
        if name not in BLACKLISTED_BUILTINS and not name.startswith("_"):
             safe_globals["__builtins__"][name] = getattr(builtins, name)

    # Pre-import allowed modules
    for mod in ALLOWED_MODULES:
        try:
            safe_globals[mod] = __import__(mod)
        except ImportError:
            pass

    try:
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
            exec(code, safe_globals)
        return_dict["output"] = output_buffer.getvalue()
        return_dict["success"] = True
    except Exception as e:
        return_dict["output"] = f"{type(e).__name__}: {str(e)}"
        return_dict["success"] = False

class SafeExecutor:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.validator = ASTValidator()

    def execute(self, code: str) -> Dict[str, Any]:
        """
        Execute python code safely.
        Returns: {"success": bool, "output": str, "error": str}
        """
        # 0. REPL-like behavior: Auto-print last expression
        try:
            tree = ast.parse(code)
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                # Wrap the last expression in print()
                # print(last_expr)
                last_expr = tree.body[-1].value
                print_call = ast.Call(
                    func=ast.Name(id='print', ctx=ast.Load()),
                    args=[last_expr],
                    keywords=[]
                )
                tree.body[-1] = ast.Expr(value=print_call)
                # Fix locations
                ast.fix_missing_locations(tree)
                code = ast.unparse(tree)
        except Exception:
            # If parsing fails here, let validator catch it or exec fail
            pass

        # 1. AST Validation
        try:
            self.validator.validate(code)
        except SecurityViolation as e:
            return {"success": False, "output": "", "error": str(e)}

        # 2. Runtime Execution (Process Isolation)
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        
        p = multiprocessing.Process(target=_safe_exec, args=(code, return_dict, self.timeout))
        p.start()
        p.join(self.timeout)

        if p.is_alive():
            p.terminate()
            p.join()
            return {"success": False, "output": "", "error": "Execution timed out."}
        
        if not return_dict:
             return {"success": False, "output": "", "error": "Process crashed or produced no result."}
             
        success = return_dict.get("success", False)
        output = return_dict.get("output", "")
        
        if success:
            return {"success": True, "output": output, "error": None}
        else:
            return {"success": False, "output": output, "error": output} # Output often contains the exception message

# Singleton instance
sandbox = SafeExecutor(timeout=5)
