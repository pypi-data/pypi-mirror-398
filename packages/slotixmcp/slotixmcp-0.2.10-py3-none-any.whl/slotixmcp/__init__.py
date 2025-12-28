"""
SlotixMCP - MCP Server for Slotix appointment management.

This package provides an MCP (Model Context Protocol) server that allows
AI assistants like Claude Desktop and ChatGPT to interact with Slotix
for managing appointments, clients, and notifications.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("slotixmcp")
except PackageNotFoundError:
    __version__ = "0.0.0"  # Development/editable install

__author__ = "Slotix"
