"""
GNS3 Web UI Iframe Component

This module provides an iframe component to embed the GNS3 Web UI
into the Streamlit application.
"""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def show_iframe(project_id: str) -> None:
    """
    Display GNS3 Web UI in an iframe.

    Args:
        project_id: The UUID of the GNS3 project to display.
    """
    # Get GNS3 server URL from environment variable
    gns3_server_url = os.getenv("GNS3_SERVER_URL", "http://127.0.0.1:3080/")

    # Build the iframe URL
    iframe_url = f"{gns3_server_url}static/web-ui/server/1/project/{project_id}"

    # Display the iframe
    st.components.v1.iframe(iframe_url, height=800, scrolling=True)
