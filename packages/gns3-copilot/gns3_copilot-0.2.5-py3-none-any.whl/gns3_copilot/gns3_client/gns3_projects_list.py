import os
from typing import Any

from dotenv import load_dotenv
from langchain.tools import BaseTool

from gns3_copilot.gns3_client import Gns3Connector
from gns3_copilot.log_config import setup_tool_logger

# Configure logging
logger = setup_tool_logger("gns3_project_list")

# load environment variables
load_dotenv()

"""
example output:

[('mylab', 'ff8e059c-c33d-47f4-bc11-c7dda8a1d500', 0, 0, 'closed'),
 ('q-learning-traffic-management', '69d49a6a-ff7f-45dd-af1e-dc14aff600cc', 0, 0, 'closed'),
 ('network_ai', 'f2f7ed27-7aa3-4b11-a64c-da947a2c7210', 6, 8, 'opened'),
 ('test', '365dd3ff-cda9-447a-94da-3a6cef75fe77', 0, 0, 'closed'),
 ('Soft-RoCE learning', 'd1e4509e-64bd-4109-b954-266223959ee9', 0, 0, 'closed')]

"""


class GNS3ProjectList(BaseTool):
    name: str = "list_gns3_projects"
    description: str = """
    Retrieves a list of all GNS3 projects with their details.
    Returns a dictionary containing a list of project information including name,
    project_name, project_id, nodes count, links count, and status.
    Example output:
        {
            "projects": [
                ("mylab", "ff8e059c-c33d-47f4-bc11-c7dda8a1d500", 0, 0, "closed"),
                ("network_ai", "f2f7ed27-7aa3-4b11-a64c-da947a2c7210", 6, 8, "opened")
            ]
        }
    """

    def _run(self, tool_input: Any = None, run_manager: Any = None) -> dict:
        try:
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

            # Return the projects data in a structured format
            projects = server.projects_summary(is_print=False)

            return {"projects": projects}

        except Exception as e:
            logger.error("Error retrieving GNS3 project list: %s", str(e))
            return {"error": f"Failed to retrieve GNS3 project list: {str(e)}"}
