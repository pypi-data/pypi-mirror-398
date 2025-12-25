"""VTK API Index - Fast in-memory index of VTK API documentation"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..utils.search import extract_description

logger = logging.getLogger(__name__)


class VTKAPIIndex:
    """Fast in-memory index of VTK API documentation"""
    
    def __init__(self, api_docs_path: Path):
        """
        Initialize the API index
        
        Args:
            api_docs_path: Path to vtk-python-docs.jsonl (raw, not chunked)
        """
        self.api_docs_path = api_docs_path
        self.classes: Dict[str, Dict[str, Any]] = {}
        self.modules: Dict[str, List[str]] = {}  # module -> [class names]
        self._load_api_docs()
    
    def _load_api_docs(self):
        """Load all API documentation from raw vtk-python-docs.jsonl"""
        logger.info(f"Loading VTK API docs from {self.api_docs_path}")
        
        if not self.api_docs_path.exists():
            logger.error(f"API docs not found at {self.api_docs_path}")
            return
        
        with open(self.api_docs_path) as f:
            for line in f:
                doc = json.loads(line)
                
                # Raw format: each line is a complete class documentation
                class_name = doc.get('class_name')
                
                if not class_name:
                    continue
                
                # Get content (full documentation with all methods)
                content = doc.get('content', '')
                module = doc.get('module_name', '')  # Raw format uses 'module_name' not 'module'
                
                # Store class info with new fields from updated JSONL format
                self.classes[class_name] = {
                    'class_name': class_name,
                    'module': module,
                    'content': content,
                    'metadata': doc,
                    'class_doc': doc.get('class_doc', ''),
                    'synopsis': doc.get('synopsis', ''),
                    'action_phrase': doc.get('action_phrase', ''),
                    'role': doc.get('role', ''),
                    'visibility_score': doc.get('visibility_score', 0.3),
                    'input_datatype': doc.get('input_datatype', ''),
                    'output_datatype': doc.get('output_datatype', ''),
                    'semantic_methods': doc.get('semantic_methods', []),
                }
                
                # Index by module
                if module:
                    if module not in self.modules:
                        self.modules[module] = []
                    self.modules[module].append(class_name)
        
        logger.info(f"Loaded {len(self.classes)} VTK classes from {len(self.modules)} modules")
    
    def get_class_info(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Get complete information about a VTK class"""
        return self.classes.get(class_name)

    def get_class_module(self, class_name: str) -> Optional[str]:
        """Return the vtkmodules.* path for a class"""
        info = self.get_class_info(class_name)
        if not info:
            return None
        return info.get('module') or info.get('metadata', {}).get('module_name')

    def get_class_methods(self, class_name: str) -> List[Dict[str, Any]]:
        """Return structured list of methods with signatures for a class"""
        info = self.get_class_info(class_name)
        if not info:
            return []

        methods = self._collect_methods_from_structured_docs(info)
        if methods:
            return methods

        return self._collect_methods_from_content(info.get('content', ''))
    
    def search_classes(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Search for classes by name or keyword
        
        Returns list of {class_name, module, description}
        """
        query_lower = query.lower()
        results = []
        
        for class_name, info in self.classes.items():
            # Match by class name
            if query_lower in class_name.lower():
                content = info['content']
                # Extract first line of description
                description = extract_description(content)
                
                results.append({
                    'class_name': class_name,
                    'module': info['module'] or 'Unknown',
                    'description': description
                })
        
        return results[:limit]
    
    def get_module_classes(self, module: str) -> List[str]:
        """Get all classes in a module"""
        return self.modules.get(module, [])
    
    def get_method_info(self, class_name: str, method_name: str) -> Optional[Dict[str, str]]:
        """Get information about a specific method of a class"""
        info = self.get_class_info(class_name)
        if not info:
            return None
        
        # Check if structured_docs exists (raw format)
        metadata = info.get('metadata', {})
        structured_docs = metadata.get('structured_docs', {})

        if structured_docs:
            # Raw format: use structured_docs
            sections = structured_docs.get('sections', {})

            # Check all method sections
            for section_name, section_data in sections.items():
                if 'methods' in section_data:
                    methods = section_data['methods']
                    if method_name in methods:
                        return {
                            'class_name': class_name,
                            'method_name': method_name,
                            'content': methods[method_name],
                            'section': section_name
                        }
        
        # Fallback: search in content (for chunked format or if structured_docs missing)
        content = info.get('content', '')
        lines = content.split('\n')
        in_methods = False
        method_lines = []
        
        for line in lines:
            if '## |  Methods defined here:' in line:
                in_methods = True
                continue
            
            if in_methods:
                if line.startswith('###') and method_name not in line:
                    # Next method, stop
                    break
                method_lines.append(line)
        
        if method_lines:
            return {
                'class_name': class_name,
                'method_name': method_name,
                'content': '\n'.join(method_lines)
            }
        
        return None
    
    def get_method_doc(self, class_name: str, method_name: str) -> Optional[str]:
        """Get just the docstring for a specific method of a class"""
        info = self.get_method_info(class_name, method_name)
        if info:
            return info.get('content', '')
        return None
    
    def get_class_doc(self, class_name: str) -> Optional[str]:
        """Get the class documentation string for a VTK class"""
        info = self.classes.get(class_name)
        if info:
            return info.get('class_doc', '')
        return None

    def get_method_signature(self, class_name: str, method_name: str) -> Optional[str]:
        """Return the canonical signature for a method if available"""
        methods = self.get_class_methods(class_name)
        for method in methods:
            if method.get('method_name') == method_name:
                signature = method.get('signature')
                if signature:
                    return signature

        # Fallback: extract first non-empty line from raw method info
        info = self.get_method_info(class_name, method_name)
        if not info:
            return None

        content = info.get('content', '')
        for line in content.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped

        return None
    
    def get_class_synopsis(self, class_name: str) -> Optional[str]:
        """Get a brief synopsis/summary of what a VTK class does"""
        info = self.classes.get(class_name)
        if info:
            return info.get('synopsis', '')
        return None
    
    def get_class_action_phrase(self, class_name: str) -> Optional[str]:
        """Get the action phrase describing what a VTK class does"""
        info = self.classes.get(class_name)
        if info:
            return info.get('action_phrase', '')
        return None
    
    def get_class_role(self, class_name: str) -> Optional[str]:
        """Get the functional role/category of a VTK class"""
        info = self.classes.get(class_name)
        if info:
            return info.get('role', '')
        return None
    
    def get_class_visibility(self, class_name: str) -> Optional[str]:
        """Get the visibility/exposure level of a VTK class"""
        info = self.classes.get(class_name)
        if info:
            return info.get('visibility_score', '')
        return None

    def get_class_input_datatype(self, class_name: str) -> Optional[str]:
        """Get the input data type for a VTK class"""
        info = self.classes.get(class_name)
        if info:
            return info.get('input_datatype', '')
        return None

    def get_class_output_datatype(self, class_name: str) -> Optional[str]:
        """Get the output data type for a VTK class"""
        info = self.classes.get(class_name)
        if info:
            return info.get('output_datatype', '')
        return None

    def get_class_semantic_methods(self, class_name: str) -> Optional[List[str]]:
        """Get the semantic methods for a VTK class"""
        info = self.classes.get(class_name)
        if info:
            return info.get('semantic_methods', [])
        return None

    def _collect_methods_from_structured_docs(self, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract method metadata from structured_docs if present"""
        methods: List[Dict[str, Any]] = []
        metadata = info.get('metadata', {})
        structured_docs = metadata.get('structured_docs', {})
        if not structured_docs:
            return methods

        sections = structured_docs.get('sections', {})
        for section_name, section_data in sections.items():
            section_methods = section_data.get('methods', {})
            for method_name, method_doc in section_methods.items():
                signature, _, description = method_doc.partition('\n\n')
                methods.append({
                    'method_name': method_name,
                    'signature': signature.strip(),
                    'doc': description.strip(),
                    'section': section_name
                })
        return methods

    def _collect_methods_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Fallback parser that walks the markdown-like content to find methods"""
        if not content:
            return []

        methods: List[Dict[str, Any]] = []
        in_methods_section = False
        current_name: Optional[str] = None
        buffer: List[str] = []

        lines = content.split('\n')
        for line in lines:
            if '## |  Methods defined here:' in line:
                in_methods_section = True
                current_name = None
                buffer = []
                continue

            if not in_methods_section:
                continue

            if line.startswith('## ') and not line.startswith('###'):
                # Leaving methods section
                break

            if line.startswith('### '):
                if current_name:
                    methods.append(self._build_method_entry(current_name, buffer))
                current_name = line[4:].strip()
                buffer = []
                continue

            if current_name is not None:
                buffer.append(line)

        if current_name:
            methods.append(self._build_method_entry(current_name, buffer))

        return [m for m in methods if m]

    @staticmethod
    def _build_method_entry(method_name: str, buffer: List[str]) -> Optional[Dict[str, Any]]:
        """Convert buffered text into a method entry"""
        if not buffer:
            return None

        signature = ''
        doc_lines: List[str] = []
        found_signature = False
        for line in buffer:
            stripped = line.strip()
            if not stripped and not found_signature:
                continue
            if not found_signature and stripped:
                signature = stripped
                found_signature = True
            else:
                doc_lines.append(line)

        if not signature:
            return None

        return {
            'method_name': method_name,
            'signature': signature,
            'doc': '\n'.join(doc_lines).strip(),
            'section': 'Methods defined here'
        }
