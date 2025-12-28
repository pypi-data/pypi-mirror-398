"""
GNS3 Copilot Agent Package

This package contains the main GNS3 Copilot agent implementation for network automation tasks.
"""

from .gns3_copilot import agent, langgraph_checkpointer

# Dynamic version management
try:
    from importlib.metadata import version

    __version__ = version("gns3-copilot")
except Exception:
    __version__ = "unknown"

__author__ = "Guobin Yue"
__description__ = "AI-powered network automation assistant for GNS3"
__url__ = "https://github.com/yueguobin/gns3-copilot"

__all__ = [
    "agent",
    "langgraph_checkpointer",
]
