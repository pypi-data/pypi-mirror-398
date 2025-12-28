"""
General Application UI Utilities for GNS3 Copilot.

This module provides common UI rendering functions used across the GNS3 Copilot
application. It includes reusable components such as the sidebar about section
and other general-purpose UI elements.

Functions:
    render_sidebar_about(): Render the About section in the sidebar displaying
                            application information and feature highlights.

Constants:
    ABOUT_TEXT: Markdown-formatted text containing application description,
                features, usage instructions, and GitHub repository link.

Example:
    Import and use in app.py:
        from gns3_copilot.ui_model.utils import render_sidebar_about

        render_sidebar_about()
"""

import streamlit as st

ABOUT_TEXT = """
GNS3 Copilot is an AI-powered assistant designed to help network engineers with
GNS3-related tasks. It leverages advanced language models to provide insights,
answer questions, and assist with network simulations.

**Features:**
- Answer GNS3-related queries
- Provide configuration examples
- Assist with troubleshooting

**Usage:**
Simply type your questions or commands in the chat interface,
and GNS3 Copilot will respond accordingly.

**Note:** This is a prototype version. For more information,
visit the [GNS3 Copilot GitHub Repository](https://github.com/yueguobin/gns3-copilot).
"""


def render_sidebar_about() -> None:
    """Render the About section in the sidebar."""
    with st.sidebar:
        st.header("About")
        st.markdown(ABOUT_TEXT)
