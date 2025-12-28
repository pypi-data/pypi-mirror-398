"""
Public module for getting device port information from GNS3 topology
"""

from typing import Any

from gns3_copilot.gns3_client import GNS3TopologyTool
from gns3_copilot.log_config import setup_tool_logger

logger = setup_tool_logger("get_gns3_device_port")


def get_device_ports_from_topology(
    device_names: list[str],
    project_id: str | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Get device connection information from GNS3 topology

    Args:
        device_names: List of device names to look up
        project_id: UUID of the specific GNS3 project to retrieve topology from

    Returns:
        Dictionary mapping device names to their connection data:
        {
            "device_name": {
                "port": console_port,
                "groups": ["cisco_IOSv_telnet"]
            }
        }
        Devices that don't exist or missing console_port will not be included
    """
    try:
        # Get topology information
        topo = GNS3TopologyTool()
        topology = topo._run(project_id=project_id)

        # Dynamically build hosts_data from topology
        hosts_data: dict[str, dict[str, Any]] = {}

        if not topology:
            logger.warning("Unable to get topology information")
            return hosts_data

        for device_name in device_names:
            # Check if device exists in topology
            if device_name not in topology.get("nodes", {}):
                logger.warning("Device '%s' not found in topology", device_name)
                continue

            node_info = topology["nodes"][device_name]
            if "console_port" not in node_info:
                logger.warning("Device '%s' missing console_port", device_name)
                continue

            # Add device to hosts_data
            hosts_data[device_name] = {
                "port": node_info["console_port"],
                "groups": ["cisco_IOSv_telnet"],
            }

        return hosts_data

    except Exception as e:
        logger.error("Error getting device port information: %s", e)
        return {}
