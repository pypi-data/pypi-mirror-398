"""
Resume Generator MCP Server

A Model Context Protocol (MCP) server for generating professional PDF resumes.
Connects to a remote API service for PDF generation - no local LibreOffice installation required.
"""

__version__ = "1.5.0"
__author__ = "Sravan Sarraju"
__description__ = "MCP server for generating professional PDF resumes from YAML/JSON data"

from .server import main

__all__ = ["main"]
