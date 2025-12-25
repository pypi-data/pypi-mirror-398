#!/usr/bin/env python3
"""
Main entry point for VTK API MCP Server

Can be run as:
  python -m vtkapi_mcp
  python -m vtkapi_mcp --api-docs path/to/docs.jsonl
"""

import asyncio
import argparse
import logging
from pathlib import Path

from .server import VTKAPIMCPServer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="VTK API MCP Server")
    parser.add_argument(
        "--api-docs",
        type=Path,
        default=Path("data/vtk-python-docs.jsonl"),
        help="Path to VTK API docs file"
    )
    
    args = parser.parse_args()
    
    server = VTKAPIMCPServer(args.api_docs)
    await server.run()


def cli():
    """Console script entry point for vtkapi-mcp."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
