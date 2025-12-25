"""Code extraction utilities for parsing Python VTK code"""

import re
from typing import List, Dict


def extract_imports(code: str) -> List[str]:
    """Extract all import statements from code"""
    imports = []
    lines = code.split('\n')
    
    in_multiline = False
    current_import = []
    
    for line in lines:
        stripped = line.strip()
        
        # Start of import
        if stripped.startswith('import ') or stripped.startswith('from '):
            current_import = [line]
            
            if '(' in line and ')' not in line:
                in_multiline = True
            else:
                imports.append(line)
                current_import = []
        
        # Continuation
        elif in_multiline:
            current_import.append(line)
            if ')' in line:
                in_multiline = False
                imports.append('\n'.join(current_import))
                current_import = []
    
    return imports


def extract_class_instantiations(code: str) -> List[str]:
    """Extract VTK class instantiations (e.g., vtkPolyDataMapper())"""
    classes = set()
    
    # Pattern: vtkClassName()
    pattern = r'\b(vtk[A-Z][a-zA-Z0-9]*)\s*\('
    matches = re.findall(pattern, code)
    classes.update(matches)
    
    return list(classes)


def extract_used_classes(code: str, available_classes: set) -> List[str]:
    """
    Extract all VTK class names that are actually used in the code
    
    Args:
        code: Python code to analyze
        available_classes: Set of valid VTK class names
    
    Returns:
        List of VTK class names found in the code
    """
    used_classes = set()
    
    # Pattern 1: Class instantiation - vtkClassName()
    pattern1 = r'\b(vtk[A-Z]\w+)\s*\('
    for match in re.finditer(pattern1, code):
        used_classes.add(match.group(1))
    
    # Pattern 2: Class usage after import - ClassName() where ClassName starts with vtk
    # This catches usage in code body
    lines = code.split('\n')
    for line in lines:
        # Skip import lines
        if 'import' in line:
            continue
        # Find vtk class usage
        for match in re.finditer(r'\b(vtk[A-Z]\w+)', line):
            class_name = match.group(1)
            # Make sure it's actually a class (in our database)
            if class_name in available_classes:
                used_classes.add(class_name)
    
    return list(used_classes)


def track_variable_types(code: str) -> Dict[str, str]:
    """
    Track variable types from VTK class instantiations
    
    Examples:
        mapper = vtkPolyDataMapper() → {'mapper': 'vtkPolyDataMapper'}
        actor = vtk.vtkActor() → {'actor': 'vtkActor'}
    
    Returns:
        Dict mapping variable names to VTK class names
    """
    var_types = {}
    lines = code.split('\n')
    
    # Pattern 1: var = vtkClassName()
    pattern1 = r'(\w+)\s*=\s*(vtk[A-Z][a-zA-Z0-9]*)\s*\('
    
    # Pattern 2: var = vtk.vtkClassName()
    pattern2 = r'(\w+)\s*=\s*vtk\.(vtk[A-Z][a-zA-Z0-9]*)\s*\('
    
    for line in lines:
        # Try pattern 1
        matches = re.findall(pattern1, line)
        for var_name, class_name in matches:
            var_types[var_name] = class_name
        
        # Try pattern 2
        matches = re.findall(pattern2, line)
        for var_name, class_name in matches:
            var_types[var_name] = class_name
    
    return var_types


def extract_method_calls_with_objects(code: str) -> List[tuple]:
    """
    Extract method calls with object references
    
    Returns:
        List of (obj_name, method_name, line) tuples
    """
    method_calls = []
    lines = code.split('\n')
    
    # Pattern: obj_name.MethodName(
    pattern = r'(\w+)\.([A-Z][a-zA-Z0-9_]*)\s*\('
    
    for line in lines:
        matches = re.findall(pattern, line)
        for obj_name, method_name in matches:
            method_calls.append((obj_name, method_name, line))
    
    return method_calls
