"""AST parser to detect stub functions."""

import ast
from dataclasses import dataclass
from typing import Any


@dataclass
class StubFunction:
    """Represents a detected stub function."""
    name: str
    args: list[str]
    arg_types: dict[str, str]  # arg_name -> type annotation string
    return_type: str | None
    docstring: str | None
    lineno: int
    
    def to_prompt_context(self) -> str:
        """Generate context string for LLM prompt."""
        parts = [f"Function: {self.name}"]
        
        # Build signature
        sig_parts = []
        for arg in self.args:
            if arg in self.arg_types:
                sig_parts.append(f"{arg}: {self.arg_types[arg]}")
            else:
                sig_parts.append(arg)
        
        sig = f"{self.name}({', '.join(sig_parts)})"
        if self.return_type:
            sig += f" -> {self.return_type}"
        parts.append(f"Signature: {sig}")
        
        if self.docstring:
            parts.append(f"Description:\n{self.docstring}")
        
        return "\n".join(parts)


def is_stub_body(body: list[ast.stmt]) -> bool:
    """Check if a function body is a stub (only contains ... or pass)."""
    if len(body) == 0:
        return True
    
    # Check for just docstring + ellipsis/pass
    real_stmts = []
    for stmt in body:
        # Skip docstrings
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            if isinstance(stmt.value.value, str):
                continue  # This is a docstring
        real_stmts.append(stmt)
    
    if len(real_stmts) == 0:
        return True
    
    if len(real_stmts) == 1:
        stmt = real_stmts[0]
        # Check for `...` (Ellipsis)
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            if stmt.value.value is ...:
                return True
        # Check for `pass`
        if isinstance(stmt, ast.Pass):
            return True
        # Check for `raise NotImplementedError`
        if isinstance(stmt, ast.Raise):
            if isinstance(stmt.exc, ast.Call):
                if isinstance(stmt.exc.func, ast.Name):
                    if stmt.exc.func.id == "NotImplementedError":
                        return True
    
    return False


def get_type_annotation(node: ast.expr | None) -> str | None:
    """Convert an AST type annotation to a string."""
    if node is None:
        return None
    return ast.unparse(node)


def extract_stub_functions(source_code: str) -> list[StubFunction]:
    """Parse source code and extract all stub functions."""
    tree = ast.parse(source_code)
    stubs = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            if is_stub_body(node.body):
                # Extract arguments
                args = []
                arg_types = {}
                
                for arg in node.args.args:
                    args.append(arg.arg)
                    if arg.annotation:
                        arg_types[arg.arg] = get_type_annotation(arg.annotation)
                
                # Extract return type
                return_type = get_type_annotation(node.returns)
                
                # Extract docstring
                docstring = ast.get_docstring(node)
                
                stubs.append(StubFunction(
                    name=node.name,
                    args=args,
                    arg_types=arg_types,
                    return_type=return_type,
                    docstring=docstring,
                    lineno=node.lineno,
                ))
    
    return stubs
