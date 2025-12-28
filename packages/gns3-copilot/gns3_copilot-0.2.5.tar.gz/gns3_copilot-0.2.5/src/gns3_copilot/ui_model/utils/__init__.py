"""
Utility modules for Streamlit UI Model in GNS3 Copilot.

This package provides utility functions and helpers that support the Streamlit
user interface components. It includes modules for configuration management,
GNS3 server connectivity checking, update management, and general UI rendering.

Modules:
    app_ui: General UI rendering functions (sidebar, about page)
    config_manager: Configuration loading and persistence to .env files
    gns3_checker: GNS3 server API connectivity validation
    update_ui: Application update checking and UI components
    updater: Core update logic (version checking, update execution)

Key Functions:
    - check_startup_updates(): Perform startup update checks
    - check_and_display_updates(): Check for updates and display results
    - render_startup_update_result(): Display update check results
    - render_update_settings(): Render update configuration UI
    - load_config_from_env(): Load configuration from .env file
    - save_config_to_env(): Save configuration to .env file
    - check_gns3_api(): Validate GNS3 server connectivity
    - render_sidebar_about(): Render sidebar about information

Example:
    Import utility functions in UI modules:
        from gns3_copilot.ui_model.utils import (
            check_gns3_api,
            load_config_from_env,
            render_update_settings,
        )
"""

from gns3_copilot.ui_model.utils.app_ui import render_sidebar_about
from gns3_copilot.ui_model.utils.config_manager import (
    ENV_FILE_PATH,
    load_config_from_env,
    save_config_to_env,
)
from gns3_copilot.ui_model.utils.gns3_checker import check_gns3_api
from gns3_copilot.ui_model.utils.update_ui import (
    check_and_display_updates,
    check_startup_updates,
    render_startup_update_result,
    render_update_settings,
)

__all__ = [
    # Update UI
    "check_startup_updates",
    "check_and_display_updates",
    "render_startup_update_result",
    "render_update_settings",
    # Config Manager
    "load_config_from_env",
    "save_config_to_env",
    "ENV_FILE_PATH",
    # GNS3 Checker
    "check_gns3_api",
    # App UI
    "render_sidebar_about",
]

# Dynamic version management
try:
    from importlib.metadata import version

    __version__ = version("gns3-copilot")
except Exception:
    __version__ = "unknown"

__author__ = "Guobin Yue"
__description__ = "AI-powered network automation assistant for GNS3"
__url__ = "https://github.com/yueguobin/gns3-copilot"
