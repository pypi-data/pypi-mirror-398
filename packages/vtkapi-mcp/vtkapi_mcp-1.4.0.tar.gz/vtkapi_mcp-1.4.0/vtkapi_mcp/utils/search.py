"""Search and text extraction utilities"""

from typing import Optional


def extract_description(content: str) -> str:
    """Extract brief description from class content"""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Find first non-header, non-module line
        if line.strip() and not line.startswith('#') and '**Module:**' not in line:
            # Take first sentence or first 100 chars
            desc = line.strip()
            if '.' in desc:
                desc = desc.split('.')[0] + '.'
            return desc[:150]
    return ""


def extract_module(content: str) -> Optional[str]:
    """Extract module path from class content"""
    # Look for "**Module:** `vtkmodules.XXX`"
    if '**Module:**' in content:
        lines = content.split('\n')
        for line in lines:
            if '**Module:**' in line:
                # Extract module from markdown code
                if '`' in line:
                    parts = line.split('`')
                    if len(parts) >= 2:
                        return parts[1].strip()
    return None
