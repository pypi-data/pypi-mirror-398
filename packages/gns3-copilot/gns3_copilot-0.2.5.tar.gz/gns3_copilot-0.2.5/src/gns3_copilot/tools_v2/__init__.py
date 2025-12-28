"""
GNS3 Copilot Tools Package

This package provides various tools for interacting with GNS3 network simulator, including:
- Device configuration command execution
- Display command execution
- Multiple device command execution using Nornir
- VPCS device configuration using telnetlib3
- Node and link management

Main modules:
- config_tools_nornir: Multiple device configuration command execution tool using Nornir
- display_tools_nornir: Multiple device command execution tool using Nornir
- vpcs_tools_telnetlib3: VPCS device configuration tool using telnetlib3 (concurrent execution)
- gns3_create_node: GNS3 node creation tool
- gns3_create_link: GNS3 link creation tool
- gns3_start_node: GNS3 node startup tool
- gns3_get_node_temp: GNS3 template retrieval tool
- linux_tools_nornir: Linux Telnet batch command execution tool using Nornir

Note: GNS3TopologyTool is now available from gns3_client package

Author: Guobin Yue
"""

# Import main tool classes
from .config_tools_nornir import ExecuteMultipleDeviceConfigCommands
from .display_tools_nornir import ExecuteMultipleDeviceCommands
from .gns3_create_link import GNS3LinkTool
from .gns3_create_node import GNS3CreateNodeTool
from .gns3_get_node_temp import GNS3TemplateTool
from .gns3_start_node import GNS3StartNodeTool
from .linux_tools_nornir import LinuxTelnetBatchTool
from .vpcs_tools_telnetlib3 import VPCSMultiCommands

# Dynamic version management
try:
    from importlib.metadata import version

    __version__ = version("gns3-copilot")
except Exception:
    __version__ = "unknown"

__author__ = "Guobin Yue"
__description__ = "AI-powered network automation assistant for GNS3"
__url__ = "https://github.com/yueguobin/gns3-copilot"

# Export main tool classes
__all__ = [
    "ExecuteMultipleDeviceConfigCommands",
    "ExecuteMultipleDeviceCommands",
    "VPCSMultiCommands",
    "GNS3CreateNodeTool",
    "GNS3LinkTool",
    "GNS3StartNodeTool",
    "GNS3TemplateTool",
    "LinuxTelnetBatchTool",
]

# Package initialization message
# print(f"GNS3 Copilot Tools package loaded (version {__version__})")
