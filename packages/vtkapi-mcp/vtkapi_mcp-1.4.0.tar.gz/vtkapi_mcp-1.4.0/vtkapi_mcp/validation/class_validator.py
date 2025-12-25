"""Class validation"""

from typing import List, Optional
from .models import ValidationError
from ..utils.extraction import extract_class_instantiations


class ClassValidator:
    """Validates VTK class usage"""
    
    def __init__(self, api_index):
        """
        Initialize class validator
        
        Args:
            api_index: VTKAPIIndex instance
        """
        self.api = api_index
    
    def validate_classes(self, code: str) -> List[ValidationError]:
        """Validate VTK class usage"""
        errors = []
        classes = extract_class_instantiations(code)
        
        for cls in classes:
            # Only validate VTK classes
            if not cls.startswith('vtk'):
                continue
            
            info = self.api.get_class_info(cls)
            if not info:
                suggestion = self._suggest_similar_class(cls)
                message = (
                    f"INVALID: Class '{cls}' not found in VTK API.\n"
                    f"  This is likely a hallucination or typo.\n\n"
                    f"  SMALLEST CHANGE: Replace '{cls}' with a valid VTK class name"
                )
                if suggestion:
                    message += f" (try: {suggestion})"
                
                errors.append(ValidationError(
                    error_type='unknown_class',
                    message=message,
                    line=None,
                    suggestion=suggestion
                ))
        
        return errors
    
    def _suggest_similar_class(self, class_name: str) -> Optional[str]:
        """Suggest similar class names for typos"""
        # Simple fuzzy search
        results = self.api.search_classes(class_name[:10], limit=3)
        
        if results:
            suggestions = [r['class_name'] for r in results]
            return f"Did you mean: {', '.join(suggestions)}?"
        
        return None
