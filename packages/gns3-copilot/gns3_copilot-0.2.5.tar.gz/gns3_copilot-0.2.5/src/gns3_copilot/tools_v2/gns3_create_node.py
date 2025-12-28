"""
GNS3 node creation tool for network topology building.

Provides functionality to create multiple nodes in GNS3 projects
using specified templates and coordinates through the GNS3 API.
"""

import json
import os
from pprint import pprint
from typing import Any

from dotenv import load_dotenv
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from gns3_copilot.gns3_client import Gns3Connector, Node
from gns3_copilot.log_config import setup_tool_logger

# Configure logging
logger = setup_tool_logger("gns3_create_node")

# Load environment variables
load_dotenv()


class GNS3CreateNodeTool(BaseTool):
    """
    A LangChain tool to create multiple nodes in a GNS3 project
    using specified templates and coordinates.

    **Input:**
    A JSON object containing the project_id and an array of nodes with template_id,
    x and y coordinates.

    Example input:
        {
            "project_id": "uuid-of-project",
            "nodes": [
                {
                    "template_id": "uuid-of-template",
                    "x": 100,
                    "y": -200
                },
                {
                    "template_id": "uuid-of-template2",
                    "x": -200,
                    "y": 300
                }
            ]
        }

    **Output:**
    A dictionary containing the creation results for all nodes.
    Example output:
        {
            "project_id": "uuid-of-project",
            "created_nodes": [
                {
                    "node_id": "uuid-of-node1",
                    "name": "NodeName1",
                    "status": "success"
                },
                {
                    "node_id": "uuid-of-node2",
                    "name": "NodeName2",
                    "status": "success"
                }
            ],
            "total_nodes": 2,
            "successful_nodes": 2,
            "failed_nodes": 0
        }
    If an error occurs during input validation, returns a dictionary with an error message.
    """

    name: str = "create_gns3_node"
    description: str = """
    Creates multiple nodes in a GNS3 project using specified templates and coordinates.
    Input is a JSON object with project_id and an array of nodes, each containing template_id, x, and y coordinates.
    Example input:
        {
            "project_id": "uuid-of-project",
            "nodes": [
                {
                    "template_id": "uuid-of-template",
                    "x": 100,
                    "y": -200
                },
                {
                    "template_id": "uuid-of-template2",
                    "x": -200,
                    "y": 300
                }
            ]
        }
    Returns a dictionary with creation results for all nodes, including success/failure status.
    If the operation fails during input validation, returns a dictionary with an error message.
    """

    def _run(
        self,
        tool_input: str,
        run_manager: CallbackManagerForToolRun | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Creates multiple nodes in a GNS3 project using the provided templates and coordinates.

        Args:
            tool_input (str): A JSON string containing project_id and an array of nodes.
            run_manager: LangChain run manager (unused).

        Returns:
            dict: A dictionary with creation results for all nodes or an error message.
        """
        try:
            # Parse input JSON
            input_data = json.loads(tool_input)
            project_id = input_data.get("project_id")
            nodes = input_data.get("nodes", [])

            # Validate input
            if not project_id:
                logger.error("Invalid input: Missing project_id.")
                return {"error": "Missing project_id."}

            if not isinstance(nodes, list) or len(nodes) == 0:
                logger.error("Invalid input: nodes must be a non-empty array.")
                return {"error": "nodes must be a non-empty array."}

            # Validate each node in the array
            for i, node_data in enumerate(nodes):
                if not isinstance(node_data, dict):
                    logger.error("Invalid input: Node %d must be a dictionary.", i + 1)
                    return {"error": f"Node {i + 1} must be a dictionary."}

                template_id = node_data.get("template_id")
                x = node_data.get("x")
                y = node_data.get("y")

                if not all(
                    [
                        template_id,
                        isinstance(x, (int, float)),
                        isinstance(y, (int, float)),
                    ]
                ):
                    logger.error(
                        "Invalid input: Node %d missing or invalid template_id, x, or y.",
                        i + 1,
                    )
                    return {
                        "error": f"Node {i + 1} missing or invalid template_id, x, or y."
                    }

            raw_version = os.getenv("API_VERSION")
            api_version = int(raw_version) if raw_version else 2  # Ensure it's int
            server_url = os.getenv("GNS3_SERVER_URL")

            # Initialize Gns3Connector
            logger.info(
                "Connecting to GNS3 server at %s...", os.getenv("GNS3_SERVER_URL")
            )

            if api_version == 2:
                gns3_server = Gns3Connector(url=server_url, api_version=api_version)
            elif api_version == 3:
                gns3_server = Gns3Connector(
                    url=server_url,
                    user=os.getenv("GNS3_SERVER_USERNAME"),
                    cred=os.getenv("GNS3_SERVER_PASSWORD"),
                    api_version=api_version,
                )
            else:
                raise ValueError(f"Unsupported API version: {api_version}")

            # Create nodes
            logger.info("Creating %d nodes in project %s...", len(nodes), project_id)
            results: list[dict[str, Any]] = []

            for i, node_data in enumerate(nodes):
                try:
                    template_id = node_data.get("template_id")
                    x = node_data.get("x")
                    y = node_data.get("y")

                    logger.info(
                        "Creating node %d/%d with template %s at coordinates (%s, %s)...",
                        i + 1,
                        len(nodes),
                        template_id,
                        x,
                        y,
                    )

                    # Create node
                    node = Node(
                        project_id=project_id,
                        template_id=template_id,
                        x=x,
                        y=y,
                        connector=gns3_server,
                    )
                    node.create()

                    # Retrieve node details
                    node.get()
                    node_info = {
                        "node_id": node.node_id,
                        "name": node.name,
                        "status": "success",
                    }

                    results.append(node_info)
                    logger.debug(
                        "Successfully created node %d: %s",
                        i + 1,
                        json.dumps(node_info, indent=2, ensure_ascii=False),
                    )

                except Exception as e:
                    error_info = {
                        "error": f"Node {i + 1} creation failed: {str(e)}",
                        "status": "failed",
                    }
                    results.append(error_info)
                    logger.error("Failed to create node %d: %s", i + 1, e)
                    # Continue with next node even if one fails

            # Calculate summary statistics
            successful_nodes = len([r for r in results if r.get("status") == "success"])
            failed_nodes = len([r for r in results if r.get("status") == "failed"])

            # Prepare final result
            final_result = {
                "project_id": project_id,
                "created_nodes": results,
                "total_nodes": len(nodes),
                "successful_nodes": successful_nodes,
                "failed_nodes": failed_nodes,
            }

            # Log the final result
            logger.info(
                "Node creation completed: %d successful, %d failed out of %d total nodes.",
                successful_nodes,
                failed_nodes,
                len(nodes),
            )
            logger.debug(
                "Final result: %s",
                json.dumps(final_result, indent=2, ensure_ascii=False),
            )

            # Return JSON-formatted result
            return final_result

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON input: %s", e)
            return {"error": f"Invalid JSON input: {e}"}
        except Exception as e:
            logger.error("Failed to process node creation request: %s", e)
            return {"error": f"Failed to process node creation request: {str(e)}"}


if __name__ == "__main__":
    # Test the tool locally with multiple nodes
    test_input = json.dumps(
        {
            "project_id": "your-project-uuid",  # Replace with actual project UUID
            "nodes": [
                {
                    "template_id": "your-template-uuid1",  # Replace with actual template UUID
                    "x": 100,
                    "y": -200,
                },
                {
                    "template_id": "your-template-uuid2",  # Replace with actual template UUID
                    "x": 200,
                    "y": -300,
                },
            ],
        }
    )
    tool = GNS3CreateNodeTool()
    result = tool._run(test_input)
    pprint(result)
