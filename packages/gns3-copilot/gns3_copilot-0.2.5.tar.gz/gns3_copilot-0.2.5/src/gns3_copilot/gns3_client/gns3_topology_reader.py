"""
This module provides a LangChain BaseTool to retrieve the topology of a
 specific GNS3 project by project ID.
"""

import copy
import os
from typing import Any

from dotenv import load_dotenv
from langchain.tools import BaseTool

from gns3_copilot.gns3_client import Gns3Connector, Project
from gns3_copilot.log_config import setup_tool_logger

# Configure logging
logger = setup_tool_logger("gns3_topology_reader")

# load environment variables
load_dotenv()


# Define LangChain tool class
class GNS3TopologyTool(BaseTool):
    """LangChain tool for retrieving GNS3 project topology information."""

    name: str = "gns3_topology_reader"
    description: str = """
    Retrieves the topology of a specific GNS3 project by project ID.

    Input: JSON string or dictionary containing:
    - `project_id` (str, required): UUID of the specific GNS3 project to retrieve topology from.
    Optional: server_url (defaults to environment variable GNS3_SERVER_URL).

    Output: A dictionary containing:
    - `project_id` (str): UUID of the project.
    - `name` (str): Project name.
    - `status` (str): Project status (e.g., 'opened', 'closed').
    - `nodes` (dict): Dictionary with node names as keys and details as values, including:
    - `node_id` (str): Node UUID.
    - `ports` (list): List of port details (e.g., `{"name": "Gi0/0", "adapter_number": int, "port_number": int, ...}`).
    - Other fields like `console_port`, `type`, `x`, `y`.
    - `links` (list): List of link details (e.g., `[{"link_id": str, "nodes": list, ...}]`), empty if no links exist.
    - If project_id is not provided or invalid: `{"error": str}`.
    - If an error occurs: `{"error": str}` (e.g., `{"error": "Failed to retrieve topology: ..."}`).

    Example Input: `{"project_id": "f32ebf3d-ef8c-4910-b0d6-566ed828cd24"}`

    Example Output*:
    {
    "project_id": "f32ebf3d-ef8c-4910-b0d6-566ed828cd24",
    "name": "network llm iosv",
    "status": "opened",
    "nodes": {
        "R-1": {
        "node_id": "e5ca32a8-9f5d-45b0-82aa-ccfbf1d1a070",
        "name": "R-1",
        "ports": [
            {'name': 'Ge 0/0', 'short_name': 'Ge 0/0'},
            {'name': 'Ge 0/1', 'short_name': 'Ge 0/1'}
        ],
        "console_port": 5000,
        "type": "qemu",
        ...
        },
        "R-2": {...}
    },
    "links": [('R-1', 'Ge 0/0', 'R-2', 'Ge 0/0'), ...]
    }
    **Note**:
    Requires a running GNS3 server at the specified URL and a valid project_id.
    Use the ports field(e.g., name: "Gi0/0") to provide input for the create_gns3_link tool.
    """

    def _run(
        self,
        tool_input: Any = None,
        run_manager: Any = None,
        project_id: str | None = None,
    ) -> dict:
        """
        Synchronous method to retrieve the topology of a specific GNS3 project.

        Args:
            tool_input : Input parameters, typically a dict or Pydantic model containing server_url.
            run_manager : Callback manager for tool run.
            project_id : The UUID of the specific GNS3 project to retrieve topology from.

        Returns:
            dict: A dictionary containing the project ID, name, status, nodes, and links,
                  or an error dictionary if an exception occurs or project_id is not provided.
        """

        try:
            # Validate project_id parameter
            if not project_id:
                logger.error("project_id parameter is required.")
                return {
                    "error": "project_id parameter is required. Please provide a valid project UUID."
                }

            api_version_str = os.getenv("API_VERSION")
            server_url = os.getenv("GNS3_SERVER_URL")

            if api_version_str == "2":
                server = Gns3Connector(
                    url=server_url,
                    api_version=int(api_version_str),  # Force convert to int
                )
            elif api_version_str == "3":
                server = Gns3Connector(
                    url=server_url,
                    user=os.getenv("GNS3_SERVER_USERNAME"),
                    cred=os.getenv("GNS3_SERVER_PASSWORD"),
                    api_version=int(api_version_str),  # Force convert to int
                )
            else:
                # Fallback handling: if API_VERSION is neither 2 nor 3
                raise ValueError(
                    f"Unsupported or missing API_VERSION: {api_version_str}"
                )

            # Use the provided project_id directly
            logger.info(f"Retrieving topology for project_id: {project_id}")
            project = Project(project_id=project_id, connector=server)
            project.get()  # Load project details

            # Get topology JSON: includes nodes (devices), links, etc.
            topology = {
                "project_id": project.project_id,
                "name": project.name,
                "status": project.status,
                "nodes": self._clean_nodes_ports(
                    copy.deepcopy(project.nodes_inventory())
                ),
                "links": project.links_summary(is_print=False),
            }
            logger.debug("Topology retrieved: %s", topology)
            return topology

        except Exception as e:
            logger.error("Error retrieving GNS3 topology: %s", str(e))
            return {"error": f"Failed to retrieve topology: {str(e)}"}

    def _clean_nodes_ports(self, data: dict) -> dict:
        """
        Clean and simplify the nodes data structure.
        Simplify each node's ports list to only keep name and short_name fields.
        """
        for node in data.values():  # Iterate through R-1, R-2, R-3, R-4
            if "ports" in node and isinstance(node["ports"], list):
                node["ports"] = [
                    {"name": port["name"], "short_name": port["short_name"]}
                    for port in node["ports"]
                ]
        return data


if __name__ == "__main__":
    from pprint import pprint

    # Test the tool
    tool = GNS3TopologyTool()

    # Example usage with project_id
    # Replace with an actual project UUID from your GNS3 server
    example_project_id = "f32ebf3d-ef8c-4910-b0d6-566ed828cd24"

    print("Testing GNS3TopologyTool with project_id...")
    result = tool._run(project_id=example_project_id)
    pprint(result)

    # Test without project_id (should return error)
    print("\nTesting without project_id (should return error)...")
    error_result = tool._run()
    pprint(error_result)
