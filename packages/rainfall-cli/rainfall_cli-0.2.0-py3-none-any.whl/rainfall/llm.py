"""LLM provider that generates and executes code."""

import json
import re
import traceback
from typing import Any

import google.generativeai as genai

from rainfall.config import RainfallConfig
from rainfall.parser import StubFunction


CODE_GEN_SYSTEM_PROMPT = """You are a Python code generator. Write the function body implementation.

CRITICAL RULES:
1. Write ONLY the function body - NO function definition, NO markdown code blocks.
2. These modules are pre-imported: os, sys, json, re, math, datetime, pathlib.Path, requests, PIL.Image
3. Use the exact parameter names provided.
4. Include a return statement.
5. Write concise, working Python code.
6. NO markdown (no ```python), just raw code.

EXAMPLE INPUT:
Function: calculate_tip(bill: float, quality: str) -> float
Description: Calculate tip based on service quality

CORRECT OUTPUT:
tip_rates = {'poor': 0.10, 'okay': 0.15, 'good': 0.18, 'excellent': 0.20}
rate = tip_rates.get(quality.lower(), 0.15)
return bill * rate

WRONG OUTPUT (has markdown):
```python
tip_rates = ...
```"""


class LLMProvider:
    """LLM provider that generates and executes code."""
    
    def __init__(self, config: RainfallConfig):
        self.config = config
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(
            model_name=config.model,
            system_instruction=CODE_GEN_SYSTEM_PROMPT,
            generation_config={
                "temperature": config.temperature,
                "max_output_tokens": 2048,
            }
        )
        self._code_cache: dict[str, str] = {}
    
    def execute_stub(self, stub: StubFunction, args: tuple, kwargs: dict) -> Any:
        """Generate code for a stub and execute it."""
        cache_key = stub.name
        
        if cache_key not in self._code_cache:
            code = self._generate_code_with_retry(stub)
            self._code_cache[cache_key] = code
            
            if self.config.verbose:
                print(f"\n[Rainfall] Generated code for {stub.name}:")
                print("-" * 40)
                print(code)
                print("-" * 40)
        else:
            code = self._code_cache[cache_key]
            if self.config.verbose:
                print(f"\n[Rainfall] Using cached code for {stub.name}")
        
        return self._execute_code(stub, code, args, kwargs)
    
    def _generate_code_with_retry(self, stub: StubFunction, max_retries: int = 2) -> str:
        """Generate code with retry on syntax errors."""
        last_error = None
        
        for attempt in range(max_retries + 1):
            code = self._generate_code(stub, error_feedback=last_error)
            
            try:
                self._validate_syntax(code)
                return code
            except SyntaxError as e:
                last_error = str(e)
                if self.config.verbose:
                    print(f"\n[Rainfall] Syntax error, retrying... ({attempt + 1}/{max_retries + 1})")
                if attempt == max_retries:
                    raise RuntimeError(f"Code generation failed after {max_retries + 1} attempts: {e}")
        
        return code
    
    def _validate_syntax(self, code: str) -> None:
        """Validate Python syntax."""
        wrapped = f"def __test__():\n{self._indent(code)}"
        compile(wrapped, "<generated>", "exec")
    
    def _generate_code(self, stub: StubFunction, error_feedback: str | None = None) -> str:
        """Generate function implementation via LLM."""
        prompt = self._build_prompt(stub, error_feedback)
        
        if self.config.verbose and not error_feedback:
            print(f"\n[Rainfall] Generating code for: {stub.name}")
        
        response = self.model.generate_content(prompt)
        raw = response.text.strip()
        
        return self._clean_code(raw)
    
    def _build_prompt(self, stub: StubFunction, error_feedback: str | None = None) -> str:
        """Build the generation prompt."""
        sig_parts = []
        for arg in stub.args:
            if arg in stub.arg_types:
                sig_parts.append(f"{arg}: {stub.arg_types[arg]}")
            else:
                sig_parts.append(arg)
        
        sig = f"{stub.name}({', '.join(sig_parts)})"
        if stub.return_type:
            sig += f" -> {stub.return_type}"
        
        parts = [f"Function: {sig}"]
        
        if stub.docstring:
            parts.append(f"Description: {stub.docstring}")
        
        if error_feedback:
            parts.append(f"\nPREVIOUS CODE HAD ERROR: {error_feedback}")
            parts.append("Fix the error and regenerate.")
        
        parts.append("\nWrite the function body (no markdown):")
        
        return "\n".join(parts)
    
    def _clean_code(self, raw: str) -> str:
        """Remove markdown and clean up generated code."""
        code = raw
        
        # Remove ```python ... ``` blocks
        pattern = r"```(?:python)?\s*\n?(.*?)```"
        matches = re.findall(pattern, code, re.DOTALL)
        if matches:
            code = matches[0]
        
        # Remove stray ``` markers
        code = code.replace("```python", "").replace("```", "")
        
        # Remove leading "python" if LLM added it
        lines = code.strip().split("\n")
        if lines and lines[0].strip().lower() == "python":
            lines = lines[1:]
        
        return "\n".join(lines).strip()
    
    def _execute_code(self, stub: StubFunction, code: str, args: tuple, kwargs: dict) -> Any:
        """Execute generated code."""
        namespace = self._build_namespace()
        
        # Inject arguments
        for i, arg_name in enumerate(stub.args):
            if i < len(args):
                namespace[arg_name] = args[i]
        namespace.update(kwargs)
        
        # Wrap in function to capture return
        wrapped = f"""
def __rainfall_fn__():
{self._indent(code)}

__result__ = __rainfall_fn__()
"""
        
        try:
            exec(wrapped, namespace)
            return namespace.get("__result__")
        except Exception as e:
            if self.config.verbose:
                print(f"\n[Rainfall] Execution error in {stub.name}:")
                traceback.print_exc()
            raise RuntimeError(f"Execution failed for {stub.name}: {e}")
    
    def _build_namespace(self) -> dict:
        """Build execution namespace with common imports."""
        namespace = {"__builtins__": __builtins__}
        
        # Standard library
        imports = """
import os
import sys
import json
import re
import math
import datetime
import html
from pathlib import Path
"""
        exec(imports, namespace)
        
        # Optional dependencies
        for imp in ["import requests", "from PIL import Image", "import numpy as np"]:
            try:
                exec(imp, namespace)
            except ImportError:
                pass
        
        return namespace
    
    def _indent(self, code: str, spaces: int = 4) -> str:
        """Indent code block."""
        indent = " " * spaces
        return "\n".join(indent + line for line in code.split("\n"))
