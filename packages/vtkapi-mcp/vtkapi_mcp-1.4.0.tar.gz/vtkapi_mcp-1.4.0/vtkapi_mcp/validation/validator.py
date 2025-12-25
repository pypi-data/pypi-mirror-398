"""Main VTK code validator"""

from pathlib import Path
from .models import ValidationResult
from .import_validator import ImportValidator
from .class_validator import ClassValidator
from .method_validator import MethodValidator
from ..utils.extraction import extract_imports


class VTKCodeValidator:
    """Validate generated VTK code using API index"""
    
    def __init__(self, api_index):
        """
        Initialize validator
        
        Args:
            api_index: Loaded VTK API index
        """
        self.api = api_index
        self.import_validator = ImportValidator(api_index)
        self.class_validator = ClassValidator(api_index)
        self.method_validator = MethodValidator(api_index)
    
    def validate_code(self, code: str) -> ValidationResult:
        """
        Validate imports, classes, and methods in generated code
        
        Args:
            code: Python code to validate
            
        Returns:
            ValidationResult with any errors found
        """
        errors = []
        
        # 1. Validate imports
        import_errors = self._validate_imports(code)
        errors.extend(import_errors)
        
        # 2. Validate class usage
        class_errors = self.class_validator.validate_classes(code)
        errors.extend(class_errors)
        
        # 3. Validate method usage
        method_errors = self.method_validator.validate_methods(code)
        errors.extend(method_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            code=code
        )
    
    def _validate_imports(self, code: str):
        """Validate all VTK import statements"""
        errors = []
        imports = extract_imports(code)
        
        for imp in imports:
            # Only validate VTK imports
            if 'vtk' not in imp.lower():
                continue
            
            # Pass full code context for smart validation
            result = self.import_validator.validate_import(imp, code_context=code)
            if not result['valid']:
                from .models import ValidationError
                errors.append(ValidationError(
                    error_type='import',
                    message=result['message'],
                    line=imp,
                    suggestion=result.get('suggested')
                ))
        
        return errors


def load_validator(api_docs_path: Path = None):
    """
    Convenience function to load validator
    
    Args:
        api_docs_path: Path to vtk-python-docs.jsonl (raw format)
                      (defaults to data/vtk-python-docs.jsonl)
    
    Returns:
        Initialized VTKCodeValidator
    """
    from ..core.api_index import VTKAPIIndex
    
    if api_docs_path is None:
        api_docs_path = Path(__file__).parent.parent.parent / "data" / "vtk-python-docs.jsonl"
    
    api_index = VTKAPIIndex(api_docs_path)
    return VTKCodeValidator(api_index)
