"""MCP Server implementation for VTK API"""

import json
import logging
from pathlib import Path
from typing import List

from mcp.server import Server
from mcp.types import TextContent

from ..core.api_index import VTKAPIIndex
from ..validation.import_validator import ImportValidator
from .tools import get_tool_definitions

logger = logging.getLogger(__name__)


class VTKAPIMCPServer:
    """MCP Server for VTK API access"""
    
    def __init__(self, api_docs_path: Path):
        self.api_index = VTKAPIIndex(api_docs_path)
        self.import_validator = ImportValidator(self.api_index)
        self.server = Server("vtk-api")
        self._setup_tools()
    
    def _setup_tools(self):
        """Register all MCP tools"""
        
        @self.server.list_tools()
        async def list_tools():
            return get_tool_definitions()
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool calls"""
            
            if name == "vtk_get_class_info":
                return self._handle_get_class_info(arguments)
            
            elif name == "vtk_search_classes":
                return self._handle_search_classes(arguments)
            
            elif name == "vtk_get_class_module":
                return self._handle_get_class_module(arguments)
            
            elif name == "vtk_get_class_methods":
                return self._handle_get_class_methods(arguments)
            
            elif name == "vtk_get_module_classes":
                return self._handle_get_module_classes(arguments)
            
            elif name == "vtk_validate_import":
                return self._handle_validate_import(arguments)
            
            elif name == "vtk_get_method_info":
                return self._handle_get_method_info(arguments)
            
            elif name == "vtk_get_method_doc":
                return self._handle_get_method_doc(arguments)
            
            elif name == "vtk_get_method_signature":
                return self._handle_get_method_signature(arguments)
            
            elif name == "vtk_get_class_doc":
                return self._handle_get_class_doc(arguments)
            
            elif name == "vtk_get_class_synopsis":
                return self._handle_get_class_synopsis(arguments)
            
            elif name == "vtk_get_class_action_phrase":
                return self._handle_get_class_action_phrase(arguments)
            
            elif name == "vtk_get_class_role":
                return self._handle_get_class_role(arguments)
            
            elif name == "vtk_get_class_visibility":
                return self._handle_get_class_visibility(arguments)
            
            elif name == "vtk_get_class_input_datatype":
                return self._handle_get_class_input_datatype(arguments)
            
            elif name == "vtk_get_class_output_datatype":
                return self._handle_get_class_output_datatype(arguments)
            
            elif name == "vtk_get_class_semantic_methods":
                return self._handle_get_class_semantic_methods(arguments)
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    def _handle_get_class_info(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_info tool call"""
        class_name = arguments["class_name"]
        info = self.api_index.get_class_info(class_name)
        
        if info:
            result = {
                "class_name": info['class_name'],
                "module": info['module'],
                "content_preview": info['content'][:500] + "...",
                "methods": info.get('methods', [])
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_search_classes(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_search_classes tool call"""
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        results = self.api_index.search_classes(query, limit)
        return [TextContent(type="text", text=json.dumps(results, indent=2))]
    
    def _handle_get_class_module(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_module tool call"""
        class_name = arguments["class_name"]
        module = self.api_index.get_class_module(class_name)
        
        if module:
            result = {
                "class_name": class_name,
                "module": module,
                "found": True
            }
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_class_methods(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_methods tool call"""
        class_name = arguments["class_name"]
        method_name = arguments.get("method_name")
        class_info = self.api_index.get_class_info(class_name)
        
        if not class_info:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        methods = self.api_index.get_class_methods(class_name)
        requested_method = None
        if method_name:
            requested_method = next(
                (m for m in methods if m['method_name'] == method_name),
                None
            )
            if not requested_method:
                method_info = self.api_index.get_method_info(class_name, method_name)
                if method_info:
                    requested_method = {
                        "method_name": method_name,
                        "content": method_info.get("content"),
                        "section": method_info.get("section")
                    }
        
        result = {
            "class_name": class_name,
            "method_count": len(methods),
            "methods": methods,
            "requested_method": requested_method,
            "method_requested": bool(method_name),
            "found": True
        }
        if method_name and requested_method is None:
            result["method_error"] = f"Method '{method_name}' not found on '{class_name}'"
            result["method_found"] = False
        else:
            result["method_found"] = bool(requested_method) if method_name else None
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_module_classes(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_module_classes tool call"""
        module = arguments["module"]
        classes = self.api_index.get_module_classes(module)
        result = {
            "module": module,
            "classes": classes,
            "count": len(classes)
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_validate_import(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_validate_import tool call"""
        import_statement = arguments["import_statement"]
        result = self.import_validator.validate_import(import_statement)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_method_info(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_method_info tool call"""
        class_name = arguments["class_name"]
        method_name = arguments["method_name"]
        info = self.api_index.get_method_info(class_name, method_name)
        
        if info:
            return [TextContent(type="text", text=json.dumps(info, indent=2))]
        else:
            result = {
                "error": f"Method '{method_name}' not found in class '{class_name}'",
                "class_name": class_name,
                "method_name": method_name,
                "found": False
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_method_doc(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_method_doc tool call - returns just the docstring"""
        class_name = arguments["class_name"]
        method_name = arguments["method_name"]
        doc = self.api_index.get_method_doc(class_name, method_name)
        
        if doc is not None:
            result = {
                "class_name": class_name,
                "method_name": method_name,
                "docstring": doc,
                "found": True
            }
        else:
            result = {
                "error": f"Method '{method_name}' not found in class '{class_name}'",
                "class_name": class_name,
                "method_name": method_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_method_signature(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_method_signature tool call"""
        class_name = arguments["class_name"]
        method_name = arguments["method_name"]
        signature = self.api_index.get_method_signature(class_name, method_name)
        result = {
            "class_name": class_name,
            "method_name": method_name,
            "signature": signature,
            "found": bool(signature)
        }
        if not signature:
            result["error"] = f"Method '{method_name}' not found in class '{class_name}'"
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_class_doc(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_doc tool call"""
        class_name = arguments["class_name"]
        doc = self.api_index.get_class_doc(class_name)
        
        if doc is not None:
            result = {
                "class_name": class_name,
                "class_doc": doc,
                "found": True
            }
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_class_synopsis(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_synopsis tool call"""
        class_name = arguments["class_name"]
        synopsis = self.api_index.get_class_synopsis(class_name)
        
        if synopsis is not None:
            result = {
                "class_name": class_name,
                "synopsis": synopsis,
                "found": True
            }
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_class_action_phrase(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_action_phrase tool call"""
        class_name = arguments["class_name"]
        action_phrase = self.api_index.get_class_action_phrase(class_name)
        
        if action_phrase is not None:
            result = {
                "class_name": class_name,
                "action_phrase": action_phrase,
                "found": True
            }
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_class_role(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_role tool call"""
        class_name = arguments["class_name"]
        role = self.api_index.get_class_role(class_name)
        
        if role is not None:
            result = {
                "class_name": class_name,
                "role": role,
                "found": True
            }
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_class_visibility(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_visibility tool call"""
        class_name = arguments["class_name"]
        visibility = self.api_index.get_class_visibility(class_name)
        
        if visibility is not None:
            result = {
                "class_name": class_name,
                "visibility": visibility,
                "found": True
            }
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_class_input_datatype(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_input_datatype tool call"""
        class_name = arguments["class_name"]
        input_datatype = self.api_index.get_class_input_datatype(class_name)
        
        if input_datatype is not None:
            result = {
                "class_name": class_name,
                "input_datatype": input_datatype,
                "found": True
            }
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_class_output_datatype(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_output_datatype tool call"""
        class_name = arguments["class_name"]
        output_datatype = self.api_index.get_class_output_datatype(class_name)
        
        if output_datatype is not None:
            result = {
                "class_name": class_name,
                "output_datatype": output_datatype,
                "found": True
            }
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    def _handle_get_class_semantic_methods(self, arguments: dict) -> List[TextContent]:
        """Handle vtk_get_class_semantic_methods tool call"""
        class_name = arguments["class_name"]
        semantic_methods = self.api_index.get_class_semantic_methods(class_name)
        
        if semantic_methods is not None:
            result = {
                "class_name": class_name,
                "semantic_methods": semantic_methods,
                "found": True
            }
        else:
            result = {
                "error": f"Class '{class_name}' not found in VTK API",
                "class_name": class_name,
                "found": False
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            logger.info("VTK API MCP Server starting...")
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
