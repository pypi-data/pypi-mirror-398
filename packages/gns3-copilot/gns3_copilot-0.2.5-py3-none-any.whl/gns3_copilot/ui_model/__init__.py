"""
Streamlit UI Model Package for GNS3 Copilot.

This package contains all Streamlit-based user interface modules for the GNS3 Copilot
application. It provides a comprehensive set of pages and utilities for managing the
entire user experience including chat interactions, settings management, and help
documentation.

Modules:
    chat: Main chat interface with AI-powered network engineering assistant
    settings: Configuration management page for GNS3, LLM, and voice settings
    help: Bilingual help documentation and configuration guide
    utils: Utility modules supporting UI functionality

The ui_model package is responsible for:
- User interface presentation and interaction
- Session state management across pages
- Settings configuration and persistence
- Help and documentation display

Example:
    The main application entry point (app.py) uses Streamlit navigation to load
    these pages dynamically:
        st.navigation([
            "ui_model/settings.py",
            "ui_model/chat.py",
            "ui_model/help.py",
        ])
"""

# Dynamic version management
try:
    from importlib.metadata import version

    __version__ = version("gns3-copilot")
except Exception:
    __version__ = "unknown"

__author__ = "Guobin Yue"
__description__ = "AI-powered network automation assistant for GNS3"
__url__ = "https://github.com/yueguobin/gns3-copilot"
