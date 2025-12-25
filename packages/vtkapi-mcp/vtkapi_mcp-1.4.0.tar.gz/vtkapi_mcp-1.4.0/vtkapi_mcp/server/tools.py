"""MCP Tool definitions for VTK API"""

from mcp.types import Tool


def get_tool_definitions():
    """Get all MCP tool definitions"""
    return [
        Tool(
            name="vtk_get_class_info",
            description="Get complete information about a VTK class including module path, description, and methods",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkPolyDataMapper')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_get_class_methods",
            description="List all methods (with signatures) for a VTK class and optionally verify a specific method",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name"
                    },
                    "method_name": {
                        "type": "string",
                        "description": "Optional method to verify existence"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_search_classes",
            description="Search for VTK classes by name or keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (e.g., 'reader', 'mapper', 'actor')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="vtk_get_class_module",
            description="Return the vtkmodules.* import path for a given VTK class",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkPolyDataMapper')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_get_module_classes",
            description="List all VTK classes in a specific module",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "Module name (e.g., 'vtkmodules.vtkRenderingCore')"
                    }
                },
                "required": ["module"]
            }
        ),
        Tool(
            name="vtk_validate_import",
            description="Validate if a VTK import statement is correct and suggest corrections",
            inputSchema={
                "type": "object",
                "properties": {
                    "import_statement": {
                        "type": "string",
                        "description": "Python import statement to validate"
                    }
                },
                "required": ["import_statement"]
            }
        ),
        Tool(
            name="vtk_get_method_info",
            description="Get documentation for a specific method of a VTK class",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name"
                    },
                    "method_name": {
                        "type": "string",
                        "description": "Method name"
                    }
                },
                "required": ["class_name", "method_name"]
            }
        ),
        Tool(
            name="vtk_get_method_doc",
            description="Get just the docstring for a specific method of a VTK class",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name"
                    },
                    "method_name": {
                        "type": "string",
                        "description": "Method name"
                    }
                },
                "required": ["class_name", "method_name"]
            }
        ),
        Tool(
            name="vtk_get_method_signature",
            description="Return only the canonical signature for a specific method of a VTK class (minimal payload)",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkSphereSource')"
                    },
                    "method_name": {
                        "type": "string",
                        "description": "Method name whose signature should be returned (e.g., 'GetOutput')"
                    }
                },
                "required": ["class_name", "method_name"]
            }
        ),
        Tool(
            name="vtk_get_class_doc",
            description="Get the class documentation string for a VTK class",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkPolyDataMapper')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_get_class_synopsis",
            description="Get a brief synopsis/summary of what a VTK class does",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkPolyDataMapper')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_get_class_action_phrase",
            description="Get the action phrase describing what a VTK class does (e.g., 'data reading', 'mesh filtering')",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkPolyDataMapper')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_get_class_role",
            description="Get the pipeline role of a VTK class. Returns one of: input, filter, properties, renderer, scene, infrastructure, output, utility, color",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkPolyDataMapper')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_get_class_visibility",
            description="Get the visibility score of a VTK class (0.0-1.0). Higher scores indicate classes more likely to be used directly.",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkPolyDataMapper')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_get_class_input_datatype",
            description="Get the input data type for a VTK class (e.g., 'vtkPolyData', 'vtkImageData')",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkPolyDataMapper')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_get_class_output_datatype",
            description="Get the output data type for a VTK class (e.g., 'vtkPolyData', 'vtkImageData')",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkContourFilter')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_get_class_semantic_methods",
            description="Get non-boilerplate callable methods for a VTK class. Excludes dunder methods, private methods, and VTK infrastructure methods.",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "VTK class name (e.g., 'vtkContourFilter')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="vtk_is_a_class",
            description="Check if a given name is a valid VTK class. Returns true if it exists in the VTK API, false otherwise.",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "Name to check (e.g., 'vtkPolyDataMapper')"
                    }
                },
                "required": ["class_name"]
            }
        )
    ]
