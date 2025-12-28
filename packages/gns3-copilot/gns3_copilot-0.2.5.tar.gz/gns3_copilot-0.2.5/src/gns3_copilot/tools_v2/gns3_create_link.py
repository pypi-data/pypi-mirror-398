"""
GNS3 link creation tool for connecting network nodes.

Provides functionality to create links between nodes in GNS3 projects
using the GNS3 API connector.
"""

import json
import os
from pprint import pprint
from typing import Any

from dotenv import load_dotenv
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from gns3_copilot.gns3_client import Gns3Connector, Link
from gns3_copilot.log_config import setup_tool_logger

# Configure logging
logger = setup_tool_logger("gns3_create_link")

# Load environment variables
load_dotenv()


class GNS3LinkTool(BaseTool):
    """
    Tool for creating network links between GNS3 nodes.

    Creates one or more links between specified nodes in a GNS3 project
    by connecting their network ports. Supports batch link creation
    with error handling for individual link failures.
    """

    name: str = "create_gns3_link"
    description: str = """
    Creates one or more links between nodes in a GNS3 project.

    Input: A JSON string with:
    - `project_id` (str): The UUID of the GNS3 project.
    - `links` (list): A non-empty array of link definitions, each containing:
    - `node_id1` (str): UUID of the first node.
    - `port1` (str): Port name of the first node (e.g., 'Ethernet0/0').
    - `node_id2` (str): UUID of the second node.
    - `port2` (str): Port name of the second node (e.g., 'Ethernet0/0').
    Note: Port names must match those retrieved from the `gns3_topology_reader` tool.

    Example Input:
    {
        "project_id": "uuid-of-project",
        "links": [
            {
                "node_id1": "uuid-of-node1",
                "port1": "Ethernet0/0",
                "node_id2": "uuid-of-node2",
                "port2": "Ethernet0/0"
            }
        ]
    }
    Output: A list of dictionaries, each containing:
    - For successfule links: link_id(str),node_id1(str),port1(str),port1(str),node_id(str),port2(str).
    - For failed links: error(str) with an error message(e.g., 'Missing required field: project_id')

    Example Output:
    [
        {
            "link_id": "uuid-of-link",
            "node_id1": "uuid-of-node1",
            "port1" : "Ethernet0/0",
            "node_id2": "uuid-of-node2",
            "port2": "Ethernet0/0"
        },
        {
            "error": "Port not found in link 1"
        },
    ]
    """

    def _run(
        self, tool_input: str, run_manager: CallbackManagerForToolRun | None = None
    ) -> list[dict[str, Any]]:
        """
        Creates one or multiple links between nodes in a GNS3 project.

        Args:
            tool_input (str): A JSON string containing project_id and links array.
            run_manager: LangChain run manager (unused).

        Returns:
            list: A list containing dictionaries with created link details or error messages.
        """
        try:
            # Parse input JSON
            input_data = json.loads(tool_input)
            project_id = input_data.get("project_id")
            links_data = input_data.get("links", [])

            # Validate input
            if not project_id:
                logger.error("Missing required field: project_id")
                return [{"error": "Missing required field: project_id"}]

            if not isinstance(links_data, list) or len(links_data) == 0:
                logger.error("Invalid links data: must be a non-empty array")
                return [{"error": "Invalid links data: must be a non-empty array"}]

            raw_api_version = os.getenv("API_VERSION")
            api_version = int(raw_api_version) if raw_api_version else 2

            # Initialize Gns3Connector
            logger.info(
                "Connecting to GNS3 server at %s...", os.getenv("GNS3_SERVER_URL")
            )

            if api_version == 2:
                gns3_server = Gns3Connector(
                    url=os.getenv("GNS3_SERVER_URL"), api_version=api_version
                )

            elif api_version == 3:
                gns3_server = Gns3Connector(
                    url=os.getenv("GNS3_SERVER_URL"),
                    user=os.getenv("GNS3_SERVER_USERNAME"),
                    cred=os.getenv("GNS3_SERVER_PASSWORD"),
                    api_version=api_version,
                )
            else:
                raise ValueError(f"Unsupported API version: {api_version}")

            created_links = []

            # Process each link definition
            for i, link_data in enumerate(links_data):
                try:
                    logger.info("Creating link %d/%d", i + 1, len(links_data))

                    # Extract link parameters
                    node_id1 = link_data.get("node_id1")
                    port1 = link_data.get("port1")
                    node_id2 = link_data.get("node_id2")
                    port2 = link_data.get("port2")

                    # Validate link parameters
                    if not all([node_id1, port1, node_id2, port2]):
                        error_msg = f"Missing required fields in link definition {i}"
                        logger.error(error_msg)
                        created_links.append({"error": error_msg})
                        continue

                    # Get node details
                    node1 = gns3_server.get_node(
                        project_id=project_id, node_id=node_id1
                    )
                    node2 = gns3_server.get_node(
                        project_id=project_id, node_id=node_id2
                    )
                    if not node1 or not node2:
                        error_msg = f"Node not found in link {i}"
                        logger.error(error_msg)
                        created_links.append({"error": error_msg})
                        continue

                    # Find port information
                    port1_info = next(
                        (
                            port
                            for port in node1.get("ports", [])
                            if port.get("name") == port1
                        ),
                        None,
                    )
                    port2_info = next(
                        (
                            port
                            for port in node2.get("ports", [])
                            if port.get("name") == port2
                        ),
                        None,
                    )
                    if not port1_info or not port2_info:
                        error_msg = f"Port not found in link {i}"
                        logger.error(error_msg)
                        created_links.append({"error": error_msg})
                        continue

                    # Create the link
                    link = Link(
                        project_id=project_id,
                        connector=gns3_server,
                        nodes=[
                            {
                                "node_id": node_id1,
                                "adapter_number": port1_info.get("adapter_number", 0),
                                "port_number": port1_info.get("port_number", 0),
                                "label": {"text": port1},
                            },
                            {
                                "node_id": node_id2,
                                "adapter_number": port2_info.get("adapter_number", 0),
                                "port_number": port2_info.get("port_number", 0),
                                "label": {"text": port2},
                            },
                        ],
                    )
                    link.create()
                    link.get()

                    # Collect link details
                    link_info = {
                        "link_id": link.link_id,
                        "node_id1": node_id1,
                        "port1": port1,
                        "node_id2": node_id2,
                        "port2": port2,
                    }
                    created_links.append(link_info)
                    logger.debug(
                        "Successfully created link: %s",
                        json.dumps(link_info, ensure_ascii=False),
                    )

                except Exception as e:
                    error_msg = f"Failed to create link {i}: {str(e)}"
                    logger.error(error_msg)
                    created_links.append({"error": error_msg})

            # Log final results
            success_count = len([link for link in created_links if "error" not in link])
            logger.info(
                "Link creation completed: %d successful, %d failed",
                success_count,
                len(links_data) - success_count,
            )

            return created_links

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON input: %s", e)
            return [{"error": f"Invalid JSON input: {e}"}]
        except Exception as e:
            logger.error("Failed to process link creation: %s", e)
            return [{"error": f"Failed to process link creation: {str(e)}"}]


if __name__ == "__main__":
    # Test with single link
    single_link_input = json.dumps(
        {
            "project_id": "your-project-uuid",
            "links": [
                {
                    "node_id1": "your-node1-uuid",
                    "port1": "Ethernet0/0",
                    "node_id2": "your-node2-uuid",
                    "port2": "Ethernet0/0",
                }
            ],
        }
    )

    # Test with multiple links
    multiple_links_input = json.dumps(
        {
            "project_id": "your-project-uuid",
            "links": [
                {
                    "node_id1": "your-node1-uuid",
                    "port1": "Ethernet0/0",
                    "node_id2": "your-node2-uuid",
                    "port2": "Ethernet0/0",
                },
                {
                    "node_id1": "your-node1-uuid",
                    "port1": "Ethernet0/1",
                    "node_id2": "your-node3-uuid",
                    "port2": "Ethernet0/0",
                },
            ],
        }
    )

    tool = GNS3LinkTool()

    print("=== Testing Single Link Creation ===")
    result = tool._run(single_link_input)
    pprint(result)

    print("\n=== Testing Multiple Links Creation ===")
    result = tool._run(multiple_links_input)
    pprint(result)
