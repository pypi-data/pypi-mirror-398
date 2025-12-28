"""
GNS3 Copilot Streamlit application entry point.

Main application module that initializes and runs the Streamlit-based web interface
with navigation between settings, chat, and help pages.
"""

import streamlit as st

from gns3_copilot.ui_model.styles import get_styles
from gns3_copilot.ui_model.utils import (
    check_startup_updates,
    render_sidebar_about,
    render_startup_update_result,
)

NAV_PAGES = [
    "ui_model/settings.py",
    "ui_model/chat.py",
    "ui_model/help.py",
]


def main() -> None:
    """Main application entry point."""
    # Set page metadata early to ensure consistent layout
    st.set_page_config(
        page_title="GNS3 Copilot",
        layout="centered",
        initial_sidebar_state="expanded",
    )

    # Apply centralized CSS styles
    st.markdown(get_styles(), unsafe_allow_html=True)

    # Check for updates on startup (blocking, runs once)
    check_startup_updates()

    # Prevent the app from crashing if a page path is missing
    try:
        pg = st.navigation(NAV_PAGES, position="sidebar")
        pg.run()
    except Exception as exc:
        st.error("Failed to initialize application navigation.")
        st.exception(exc)
        st.stop()

    # Display update result only on Settings page
    if hasattr(pg, "script_path") and pg.script_path == "ui_model/settings.py":
        render_startup_update_result()

    # Render sidebar content
    render_sidebar_about()


if __name__ == "__main__":
    main()
