"""Method validation"""

from typing import List, Optional
from .models import ValidationError
from ..utils.extraction import track_variable_types, extract_method_calls_with_objects


class MethodValidator:
    """Validates VTK method calls"""
    
    def __init__(self, api_index):
        """
        Initialize method validator
        
        Args:
            api_index: VTKAPIIndex instance
        """
        self.api = api_index
    
    def validate_methods(self, code: str) -> List[ValidationError]:
        """
        Validate VTK method calls using type tracking
        
        Strategy:
        1. Track variable types from instantiations (e.g., mapper = vtkPolyDataMapper())
        2. Validate method calls against the tracked type (e.g., mapper.SetInputData())
        3. Use MCP's get_method_info(class_name, method_name) to check validity
        """
        errors = []
        
        # Step 1: Track variable types from instantiations
        var_types = track_variable_types(code)
        
        # Step 2: Extract method calls with object references
        method_calls = extract_method_calls_with_objects(code)
        
        for obj_name, method_name, line in method_calls:
            # Get the type of the object
            class_name = var_types.get(obj_name)
            if not class_name:
                # Can't determine type, skip validation
                continue
            
            # Check if this method exists for this class
            method_info = self.api.get_method_info(class_name, method_name)
            if not method_info:
                # Find similar methods from the same class
                suggestion = self._suggest_similar_method(class_name, method_name)
                
                # Create strong, actionable error message
                if suggestion:
                    message = (
                        f"method: INVALID: Method '{method_name}()' doesn't exist on '{class_name}'.\n"
                        f"  REPLACE THIS EXACT LINE:\n"
                        f"    {line.strip()}\n"
                        f"  WITH:\n"
                        f"    {line.strip().replace(method_name, suggestion)}\n\n"
                        f"  REQUIRED: Change '{method_name}' to '{suggestion}' - this is the correct method name."
                    )
                else:
                    message = (
                        f"method: INVALID: Method '{method_name}()' doesn't exist on '{class_name}'.\n"
                        f"  REMOVE THIS LINE:\n"
                        f"    {line.strip()}\n\n"
                        f"  REQUIRED: Delete this line completely - this method does not exist in VTK."
                    )
                
                errors.append(ValidationError(
                    error_type='method',
                    message=message,
                    line=line.strip() if line else None,
                    suggestion=suggestion
                ))
        
        return errors
    
    def _suggest_similar_method(self, class_name: str, method_name: str) -> Optional[str]:
        """
        Suggest similar method names from the actual class
        
        Args:
            class_name: VTK class name (e.g., 'vtkExodusIIReader')
            method_name: Invalid method name to find alternatives for
            
        Returns:
            Suggested method name or None
        """
        # Get all valid methods from the class
        class_info = self.api.get_class_info(class_name)
        if not class_info:
            return None
        
        # Extract methods from structured_docs
        valid_methods = []
        metadata = class_info.get('metadata', {})
        structured_docs = metadata.get('structured_docs', {})
        if structured_docs:
            sections = structured_docs.get('sections', {})
            for section_data in sections.values():
                if 'methods' in section_data:
                    valid_methods.extend(section_data['methods'].keys())
        
        if not valid_methods:
            return None
        
        # First try exact match (case-insensitive)
        for valid_method in valid_methods:
            if valid_method.lower() == method_name.lower():
                return valid_method
        
        # Try fuzzy match using difflib
        import difflib
        close_matches = difflib.get_close_matches(method_name, valid_methods, n=1, cutoff=0.6)
        if close_matches:
            return close_matches[0]
        
        # Try finding methods with similar prefix
        method_prefix = method_name[:4]  # First 4 chars
        similar_prefix = [m for m in valid_methods if m.startswith(method_prefix)]
        if similar_prefix:
            return similar_prefix[0]
        
        return None
