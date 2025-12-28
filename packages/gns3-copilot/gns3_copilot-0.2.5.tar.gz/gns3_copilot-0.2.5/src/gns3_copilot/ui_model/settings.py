"""
Streamlit-based settings management module for GNS3 Copilot application.

This module provides a comprehensive configuration interface for managing GNS3 server
connections, LLM model settings, and application preferences. It handles loading and
saving configuration to/from .env files, validates input parameters, and maintains
session state for persistent settings across the Streamlit application.

Key Features:
- GNS3 server configuration (host, URL, API version, authentication)
- LLM model provider setup with support for multiple providers
- Environment variable management and persistence
- Input validation and error handling
- Streamlit UI components for interactive configuration
"""

import streamlit as st

from gns3_copilot.log_config import setup_logger
from gns3_copilot.ui_model.utils import (
    ENV_FILE_PATH,
    check_gns3_api,
    load_config_from_env,
    render_update_settings,
    save_config_to_env,
)
from gns3_copilot.ui_model.utils.config_manager import (
    STT_MODELS,
    STT_RESPONSE_FORMATS,
    TTS_MODELS,
    TTS_VOICES,
)

logger = setup_logger("settings")

# Initialization
if "GNS3_SERVER_HOST" not in st.session_state:
    logger.info("Initializing Settings page - loading configuration")
    load_config_from_env()
else:
    logger.debug("Settings page already initialized")

# Streamlit UI
st.title("GNS3 Copilot Settings")
st.info(f"Configuration file path: **{ENV_FILE_PATH}**")

with st.expander("GNS3 Copilot Updates", expanded=True):
    render_update_settings()

with st.expander("GNS3 API Settings", expanded=True):
    # GNS3 Server address/API point
    col1, col2 = st.columns([1, 2])
    with col1:
        st.text_input(
            "GNS3 Server Host *",
            key="GNS3_SERVER_HOST",
            type="default",
            placeholder="E.g., 127.0.0.1",
        )
    with col2:
        st.text_input(
            "GNS3 Server URL *",
            key="GNS3_SERVER_URL",
            type="default",
            placeholder="E.g., http://127.0.0.1:3080 or http://127.0.0.1:8000",
        )

    # GNS3 API version select
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        st.selectbox("GNS3 API Version", ["2", "3"], key="API_VERSION")

    if st.session_state.get("API_VERSION") == "3":
        with col2:
            st.text_input(
                "GNS3 User *",
                key="GNS3_SERVER_USERNAME",
                type="default",
                placeholder="E.g., admin",
            )
        with col3:
            st.text_input(
                "GNS3 Password *",
                key="GNS3_SERVER_PASSWORD",
                type="password",
                placeholder="E.g., admin",
            )
    else:
        pass

    # Button to manually check if GNS3 API is reachable
    if st.button("Check GNS3 API"):
        check_gns3_api()

with st.expander("LLM Model Configuration", expanded=True):
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        # LLM Model Provider
        st.text_input(
            "Model Provider *",  # Updated to use * for required field
            key="MODE_PROVIDER",
            type="default",
            help="""
    Supported model_provider values and the corresponding integration package are:

    openai,
    anthropic,
    ollama,
    deepseek,
    xai...

    If using the 'OpenRouter' platform, please enter 'openai' here.
            """,
            placeholder="e.g. 'deepseek', 'openai'",
        )

    with col2:
        # LLM Model Name
        st.text_input(
            "Model Name *",
            key="MODEL_NAME",
            type="default",
            help="""
The name or ID of the model, e.g. 'o3-mini', 'claude-sonnet-4-5-20250929', 'deepseek-caht'.

If using the OpenRouter platform,
please enter the model name in the OpenRouter format,
e.g.: 'openai/gpt-4o-mini', 'x-ai/grok-4-fast'.
            """,
            placeholder="e.g. 'o3-mini', 'claude-sonnet-4-5-20250929', 'deepseek-caht'",
        )

    with col3:
        # LLM model temperature
        st.text_input(
            "Model Temperature",
            key="TEMPERATURE",
            type="default",
            help="""
Controls randomness: higher values mean more random output. Typical range is 0.0 to 1.0.
            """,
        )

    # LLM model provider base url
    st.text_input(
        "Base Url",
        key="BASE_URL",
        type="default",
        help="""
To use OpenRouter, the Base Url must be entered, e.g., https://openrouter.ai/api/v1.
        """,
        placeholder="e.g., OpenRouter https://openrouter.ai/api/v1",
    )

    # LLM API KEY
    st.text_input(
        "Model API Key *",
        key="MODEL_API_KEY",
        type="password",
        help="""
The key required for authenticating with the model's provider.
This is usually issued when you sign up for access to the model.
        """,
    )

with st.expander("Voice Settings (TTS/STT)", expanded=True):
    # Voice Enable/Disable Toggle
    st.caption("Voice Control")
    voice_enabled = st.checkbox(
        "Enable Voice Features (TTS/STT)",
        value=st.session_state.get("VOICE", False),
        help="""
Enable or disable voice features including:
- **Text-to-Speech (TTS)**: Convert AI responses to speech
- **Speech-to-Text (STT)**: Convert voice input to text

When disabled, all voice-related settings below will be hidden.
        """,
    )

    # Update session state with boolean value
    st.session_state["VOICE"] = voice_enabled

    # Show voice settings only when voice is enabled
    if voice_enabled:
        st.markdown("---")  # Separator

        # TTS Configuration Section
        st.caption("Text-to-Speech (TTS) Configuration")

        # TTS First row: API Key, Model, Voice
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.text_input(
                "TTS API Key",
                key="TTS_API_KEY",
                type="password",
                help="""
API key for TTS service authentication.
Leave empty for local/dummy services.
                """,
                placeholder="Enter your TTS API key",
            )
        with col2:
            st.selectbox(
                "TTS Model",
                options=[""] + TTS_MODELS,
                key="TTS_MODEL",
                help="""
Select the TTS model to use:
- **tts-1**: Standard quality, faster
- **tts-1-hd**: High quality, slower
- **gpt-4o-mini-tts**: Latest model with voice instructions support
                """,
            )
        with col3:
            st.selectbox(
                "TTS Voice",
                options=[""] + TTS_VOICES,
                key="TTS_VOICE",
                help="""
Select the voice persona for TTS output.
Different voices have different tones and characteristics.
                """,
            )

        # TTS Second row: Base URL and Speed
        col1, col2 = st.columns([2, 1])
        with col1:
            st.text_input(
                "TTS Base URL",
                key="TTS_BASE_URL",
                type="default",
                help="""
Base URL for the TTS API endpoint.
Use local TTS service endpoints like http://localhost:4123/v1
                """,
                placeholder="e.g., http://localhost:4123/v1",
            )
        with col2:
            st.slider(
                "TTS Speed",
                min_value=0.25,
                max_value=4.0,
                value=1.0,
                step=0.25,
                key="TTS_SPEED",
                help="""
Controls the speed of speech synthesis:
- 0.25: Very slow
- 1.0: Normal speed
- 4.0: Very fast
                """,
            )

        # STT Configuration Section
        st.markdown("---")  # Separator
        st.caption("Speech-to-Text (STT) Configuration")

        # STT First row: API Key, Model, Language
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.text_input(
                "STT API Key",
                key="STT_API_KEY",
                type="password",
                help="""
API key for STT service authentication.
Leave empty for local/dummy services.
                """,
                placeholder="Enter your STT API key",
            )
        with col2:
            st.selectbox(
                "STT Model",
                options=[""] + STT_MODELS,
                key="STT_MODEL",
                help="""
Select the STT model to use:
- **whisper-1**: Standard Whisper model
- **gpt-4o-transcribe**: GPT-4 based transcription
- **gpt-4o-transcribe-diarize**: With speaker diarization
                """,
            )
        with col3:
            st.text_input(
                "STT Language",
                key="STT_LANGUAGE",
                type="default",
                help="""
ISO 639-1 language code (e.g., 'en', 'zh', 'ja').
Leave empty for auto-detection.
                """,
                placeholder="e.g., en, zh, ja (optional)",
            )

        # STT Second row: Base URL, Temperature, Response Format
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.text_input(
                "STT Base URL",
                key="STT_BASE_URL",
                type="default",
                help="""
Base URL for the STT API endpoint.
Use local STT service endpoints like http://127.0.0.1:8001/v1
                """,
                placeholder="e.g., http://127.0.0.1:8001/v1",
            )
        with col2:
            st.slider(
                "STT Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                key="STT_TEMPERATURE",
                help="""
Controls randomness in transcription:
- 0.0: Deterministic, most accurate
- 1.0: More creative, less accurate
                """,
            )
        with col3:
            st.selectbox(
                "STT Response Format",
                options=[""] + STT_RESPONSE_FORMATS,
                key="STT_RESPONSE_FORMAT",
                help="""
Output format for transcription results:
- **json**: Standard JSON with text
- **text**: Plain text only
- **verbose_json**: JSON with timestamps
- **srt/vtt**: Subtitle formats
                """,
            )
    else:
        st.info(
            "💡 **Voice features are currently disabled.** Enable the toggle above to configure TTS/STT settings."
        )

with st.expander("Other Settings", expanded=True):
    english_levels = ["Normal Prompt", "A1", "A2", "B1", "B2", "C1", "C2"]
    st.selectbox(
        "English Level",
        options=english_levels,
        key="ENGLISH_LEVEL",
        help="""
Select your English proficiency level based on the CEFR (Common European Framework of Reference for Languages) framework:

**CEFR English Levels:**
- **A1 (Beginner)**: Basic phrases, simple network terminology
- **A2 (Elementary)**: Simple sentences, common network concepts
- **B1 (Intermediate)**: Complex sentences, technical explanations
- **B2 (Upper-Intermediate)**: Professional network terminology
- **C1 (Advanced)**: Expert-level network discussions
- **C2 (Proficiency)**: Native-level technical communication

**Auto Select**: Uses the standard network automation prompt (React Prompt) optimized for general technical users

The system will adjust prompt complexity, vocabulary, and explanation style based on your selected level.
""",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        st.text_input(
            "Linux Console Username",
            key="LINUX_TELNET_USERNAME",
            placeholder="E.g., debian",
            type="default",
            help="""
Use gns3 debian linux.

https://www.gns3.com/marketplace/appliances/debian-2
            """,
        )
    with col2:
        st.text_input(
            "Linux Console Password",
            key="LINUX_TELNET_PASSWORD",
            placeholder="E.g., debian",
            type="password",
        )

if ENV_FILE_PATH:
    st.button("Save Settings to .env", on_click=save_config_to_env)
else:
    # Cannot find or create the .env file, so the save button is disabled.
    st.error(
        "Could not find or create the .env file, so the save button has been disabled."
    )
