#!/usr/bin/env python3
"""
PyBr - Python with Braces Runtime Transformer
Allows .pybr files to use {} syntax that transforms to Python : syntax at runtime

Usage:
    1. Write code in .pybr files using braces
    2. Import this module to enable .pybr support
    3. Run .pybr files directly or import them

Example .pybr file:
    def my_function() {
        if True {
            print("Hello World")
        } else {
            print("Goodbye")
        }
    }
"""

import sys
import os
import importlib.util
import importlib.machinery
from importlib.abc import Loader, MetaPathFinder
import re
import ast
import tokenize
import io
from typing import List, Tuple, Optional, Dict
import traceback

__version__ = "1.1.4"
__author__ = "Md Abu Salehin"
__email__ = "mdabusalehin123@gmail.com"

class PyBrTransformer:
    """
    Core transformer that converts brace syntax to Python syntax
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.line_mapping: Dict[int, int] = {}
        self.valid_constructs = [
            'def', 'class', 'if', 'elif', 'else', 'while', 
            'for', 'try', 'except', 'finally', 'with', 
            'match', 'case'
        ]
    
    def transform(self, source_code: str, filename: str = "<string>") -> str:
        """
        Transform .pybr brace syntax to Python colon syntax
        
        Args:
            source_code: Source code with brace syntax
            filename: Filename for error reporting
            
        Returns:
            Valid Python code
        """
        try:
            return self._transform_with_stack(source_code, filename)
        except Exception as e:
            if self.debug:
                print(f"Transform error in {filename}: {e}")
            raise
    
    def _transform_with_stack(self, source_code: str, filename: str) -> str:
        """Transform using a stack-based approach for proper nesting"""
        lines = source_code.split('\n')
        result = []
        brace_stack = []  # Stack: [(indent_level, line_num, construct_type)]
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            line = line.rstrip()
            
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                result.append(original_line)
                continue
            
            # First handle combined closing/opening patterns like }else{
            transformed = self._handle_combined_braces(line, line_num, brace_stack, filename)
            if transformed:
                result.append(transformed)
                continue
            
            # Handle regular opening braces
            transformed = self._handle_opening_brace(line, line_num, brace_stack)
            if transformed:
                result.append(transformed)
                continue
            
            # Handle closing braces
            if self._is_closing_brace_line(line):
                if not brace_stack:
                    raise SyntaxError(f"Unmatched closing brace at line {line_num} in {filename}")
                brace_stack.pop()
                continue
            
            # Regular line - keep as is
            result.append(original_line)
        
        # Check for unmatched opening braces
        if brace_stack:
            unmatched = brace_stack[-1]
            raise SyntaxError(f"Unmatched opening brace at line {unmatched[1]} in {filename}")
        
        transformed_code = '\n'.join(result)
        
        # Validate the transformed code
        try:
            compile(transformed_code, filename, 'exec')
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in {filename}: {e}")
        
        return transformed_code
    
    def _handle_combined_braces(self, line: str, line_num: int, 
                              brace_stack: list, filename: str) -> Optional[str]:
        """
        Handle combined closing/opening brace patterns like:
        } else {
        } elif condition {
        } catch(Exception e) {
        """
        match = re.match(r'^(\s*)(}\s*)(\w+)(?:\s+([^{]+))?\s*{\s*$', line)
        if not match:
            return None
            
        indent = len(match.group(1))
        keyword = match.group(3).strip()
        condition = (match.group(4) or "").strip()
        
        # Handle closing brace part
        if not brace_stack:
            raise SyntaxError(f"Unmatched closing brace at line {line_num} in {filename}")
        brace_stack.pop()
        
        # Handle opening part
        new_line = ' ' * indent + keyword
        if condition:
            new_line += ' ' + condition
        new_line += ':'
        
        # Validate construct if it's a known Python keyword
        if keyword in self.valid_constructs:
            brace_stack.append((indent, line_num, keyword))
        else:
            brace_stack.append((indent, line_num, 'block'))
        
        return new_line
    
    def _handle_opening_brace(self, line: str, line_num: int, 
                            brace_stack: list) -> Optional[str]:
        """Handle lines with opening braces"""
        if '{' not in line:
            return None
            
        brace_pos = line.find('{')
        before_brace = line[:brace_pos].strip()
        if not before_brace:
            return None
            
        # Check for standard Python constructs
        for construct in self.valid_constructs:
            if before_brace == construct or before_brace.startswith(construct + ' '):
                indent = len(line) - len(line.lstrip())
                new_line = ' ' * indent + before_brace + ':'
                brace_stack.append((indent, line_num, construct))
                return new_line
        
        # Handle other constructs (like Java-style catch blocks)
        other_match = re.match(r'^(\s*)(\w+)(?:\s+([^{]+))?\s*{', line)
        if other_match:
            indent = len(other_match.group(1))
            keyword = other_match.group(2)
            condition = (other_match.group(3) or "").strip()
            
            new_line = ' ' * indent + keyword
            if condition:
                new_line += ' ' + condition
            new_line += ':'
            brace_stack.append((indent, line_num, 'block'))
            return new_line
        
        return None
    
    def _is_closing_brace_line(self, line: str) -> bool:
        """Check if line contains only a closing brace"""
        return bool(re.match(r'^\s*}\s*(?:#.*)?$', line))


class PyBrLoader(Loader):
    """Custom loader for .pybr files"""
    
    def __init__(self, fullname: str, path: str, debug: bool = False):
        self.fullname = fullname
        self.path = path
        self.transformer = PyBrTransformer(debug)
    
    def create_module(self, spec):
        """Create module - use default behavior"""
        return None
    
    def exec_module(self, module):
        """Execute the .pybr module after transformation"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            transformed_source = self.transformer.transform(source, self.path)
            compiled = compile(transformed_source, self.path, 'exec')
            exec(compiled, module.__dict__)
            
        except Exception as e:
            raise ImportError(f"Error loading {self.path}: {e}")


class PyBrMetaFinder(MetaPathFinder):
    """Meta path finder for .pybr files"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def find_spec(self, fullname, path, target=None):
        """Find .pybr files and create specs for them"""
        if path is None:
            path = sys.path
        
        for search_path in path:
            if not os.path.isdir(search_path):
                continue
            
            pybr_path = os.path.join(search_path, fullname + '.pybr')
            if os.path.exists(pybr_path):
                loader = PyBrLoader(fullname, pybr_path, self.debug)
                spec = importlib.machinery.ModuleSpec(fullname, loader)
                spec.origin = pybr_path
                return spec
        
        return None


class PyBrRunner:
    """Main class for running .pybr files"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.transformer = PyBrTransformer(debug)
        self.finder = None
    
    def enable_import_hook(self):
        """Enable importing .pybr files"""
        if self.finder is None:
            self.finder = PyBrMetaFinder(self.debug)
            sys.meta_path.insert(0, self.finder)
    
    def disable_import_hook(self):
        """Disable importing .pybr files"""
        if self.finder and self.finder in sys.meta_path:
            sys.meta_path.remove(self.finder)
            self.finder = None
    
    def run_file(self, filepath: str, globals_dict: dict = None):
        """Run a .pybr file directly"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        transformed = self.transformer.transform(source, filepath)
        
        if globals_dict is None:
            globals_dict = {
                '__file__': filepath,
                '__name__': '__main__',
                '__package__': None,
            }
        
        try:
            compiled = compile(transformed, filepath, 'exec')
            exec(compiled, globals_dict)
        except Exception as e:
            if self.debug:
                print(f"Execution error: {e}")
                traceback.print_exc()
            raise
    
    def transform_file(self, input_path: str, output_path: str = None) -> str:
        """Transform a .pybr file to .py file"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"File not found: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        transformed = self.transformer.transform(source, input_path)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transformed)
        
        return transformed


# Global instance
_pybr_runner = None

def enable_pybr(debug: bool = False):
    """Enable .pybr file support globally"""
    global _pybr_runner
    _pybr_runner = PyBrRunner(debug)
    _pybr_runner.enable_import_hook()

def disable_pybr():
    """Disable .pybr file support"""
    global _pybr_runner
    if _pybr_runner:
        _pybr_runner.disable_import_hook()
        _pybr_runner = None

def run_pybr(filepath: str, globals_dict: dict = None):
    """Run a .pybr file"""
    runner = PyBrRunner()
    runner.run_file(filepath, globals_dict)

def transform_pybr(source_code: str, filename: str = "<string>") -> str:
    """Transform .pybr source code to Python"""
    transformer = PyBrTransformer()
    return transformer.transform(source_code, filename)

def convert_pybr_to_py(input_path: str, output_path: str = None) -> str:
    """Convert .pybr file to .py file"""
    runner = PyBrRunner()
    return runner.transform_file(input_path, output_path)

# Convenience aliases
transform_code = transform_pybr

# Public API
__all__ = [
    'PyBrTransformer',
    'PyBrLoader',
    'PyBrMetaFinder',
    'PyBrRunner',
    'enable_pybr',
    'disable_pybr',
    'run_pybr',
    'transform_pybr',
    'transform_code',
    'convert_pybr_to_py',
]