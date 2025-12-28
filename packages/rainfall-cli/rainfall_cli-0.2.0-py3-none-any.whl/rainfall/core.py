"""Core execution logic for Rainfall."""

import ast
import sys
from pathlib import Path
from typing import Any

from rainfall.config import RainfallConfig
from rainfall.parser import extract_stub_functions, StubFunction
from rainfall.llm import LLMProvider


class StubTransformer(ast.NodeTransformer):
    """Transform stub function definitions to use our LLM-powered wrappers."""
    
    def __init__(self, stub_names: set[str]):
        self.stub_names = stub_names
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Remove stub function definitions (they'll be provided in namespace)."""
        if node.name in self.stub_names:
            # Return None to remove this node from the AST
            return None
        return self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        """Handle async stub functions too."""
        if node.name in self.stub_names:
            return None
        return self.generic_visit(node)


def execute_with_rainfall(script_path: Path, config: RainfallConfig) -> None:
    """Execute a Python script with Rainfall-powered stub functions."""
    source_code = script_path.read_text(encoding="utf-8")
    
    # Find all stub functions
    stubs = extract_stub_functions(source_code)
    
    if config.dry_run:
        _print_stubs(stubs)
        return
    
    if config.verbose and stubs:
        print(f"[Rainfall] Found {len(stubs)} stub function(s): {[s.name for s in stubs]}")
    
    # Create LLM provider
    llm = LLMProvider(config)
    
    # Build stub lookup
    stub_lookup = {stub.name: stub for stub in stubs}
    stub_names = set(stub_lookup.keys())
    
    # Transform AST to remove stub function definitions
    tree = ast.parse(source_code)
    transformer = StubTransformer(stub_names)
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    
    # Create the execution namespace with our wrappers
    namespace = _create_namespace(stub_lookup, llm, config)
    
    # Add script's directory to path for imports
    script_dir = str(script_path.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Execute the transformed script
    exec(compile(transformed_tree, script_path, "exec"), namespace)


def _print_stubs(stubs: list[StubFunction]) -> None:
    """Print detected stub functions (dry-run mode)."""
    if not stubs:
        print("[Rainfall] No stub functions found.")
        return
    
    print(f"[Rainfall] Found {len(stubs)} stub function(s):\n")
    
    for stub in stubs:
        print(f"  Line {stub.lineno}: {stub.name}")
        
        # Build signature display
        sig_parts = []
        for arg in stub.args:
            if arg in stub.arg_types:
                sig_parts.append(f"{arg}: {stub.arg_types[arg]}")
            else:
                sig_parts.append(arg)
        sig = f"({', '.join(sig_parts)})"
        if stub.return_type:
            sig += f" -> {stub.return_type}"
        print(f"    Signature: {stub.name}{sig}")
        
        if stub.docstring:
            # Show first line of docstring
            first_line = stub.docstring.split('\n')[0].strip()
            print(f"    Docstring: {first_line}")
        
        print()


def _create_namespace(
    stub_lookup: dict[str, StubFunction],
    llm: LLMProvider,
    config: RainfallConfig,
) -> dict[str, Any]:
    """Create the execution namespace with Rainfall-powered functions."""
    namespace = {
        "__name__": "__main__",
        "__builtins__": __builtins__,
    }
    
    # Create wrapper functions for each stub
    for name, stub in stub_lookup.items():
        namespace[name] = _create_stub_wrapper(stub, llm, config)
    
    return namespace


def _create_stub_wrapper(
    stub: StubFunction,
    llm: LLMProvider,
    config: RainfallConfig,
):
    """Create a wrapper function that calls the LLM for a stub."""
    def wrapper(*args, **kwargs):
        return llm.execute_stub(stub, args, kwargs)
    
    # Preserve function metadata
    wrapper.__name__ = stub.name
    wrapper.__doc__ = stub.docstring
    
    return wrapper
