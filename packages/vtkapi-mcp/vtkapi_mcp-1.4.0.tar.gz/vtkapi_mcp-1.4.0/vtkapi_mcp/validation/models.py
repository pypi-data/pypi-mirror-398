"""Validation data models"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ValidationError:
    """Single validation error"""
    error_type: str  # 'import', 'unknown_class', 'unknown_method'
    message: str
    line: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of code validation"""
    is_valid: bool
    errors: List[ValidationError]
    code: str
    
    @property
    def has_errors(self):
        return len(self.errors) > 0
    
    def format_errors(self) -> str:
        """Format errors for LLM correction prompt"""
        if not self.errors:
            return "No errors found."
        
        formatted = []
        for i, error in enumerate(self.errors, 1):
            formatted.append(f"{i}. {error.error_type.upper()}: {error.message}")
            if error.line:
                formatted.append(f"   Line: {error.line}")
            if error.suggestion:
                formatted.append(f"   Suggestion: {error.suggestion}")
        
        return "\n".join(formatted)
