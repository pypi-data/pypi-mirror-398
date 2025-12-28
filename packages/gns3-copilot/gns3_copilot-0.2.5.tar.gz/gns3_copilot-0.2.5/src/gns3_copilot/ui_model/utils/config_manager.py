"""
Configuration Management Module for GNS3 Copilot.

This module handles loading, saving, and validating application configuration
settings for the GNS3 Copilot application. It provides functions to manage
configuration stored in .env files, including GNS3 server settings, LLM model
configurations, voice settings (TTS/STT), and other application preferences.

Key Functions:
    load_config_from_env(): Load configuration from .env file into session state
    save_config_to_env(): Save current session state configuration to .env file

Configuration Categories:
    - GNS3 Server: Host, URL, API version, authentication credentials
    - LLM Model: Provider, model name, API key, base URL, temperature
    - Voice (TTS): API key, model, voice, base URL, speed settings
    - Voice (STT): API key, model, language, base URL, temperature, response format
    - Other: Linux console credentials, English proficiency level

Constants:
    CONFIG_MAP: Mapping between Streamlit widget keys and .env variable names
    MODEL_PROVIDERS: List of supported LLM model providers
    TTS_MODELS: Supported text-to-speech models
    TTS_VOICES: Available voice options for TTS
    STT_MODELS: Supported speech-to-text models
    STT_RESPONSE_FORMATS: Available output formats for STT
    ENV_FILE_PATH: Path to the .env configuration file

Example:
    Load configuration at application startup:
        from gns3_copilot.ui_model.utils import load_config_from_env

        load_config_from_env()  # Loads config into st.session_state

    Save configuration after user modifies settings:
        from gns3_copilot.ui_model.utils import save_config_to_env

        save_config_to_env()  # Persists session state to .env file
"""

import os

import streamlit as st
from dotenv import find_dotenv, load_dotenv, set_key

from gns3_copilot.log_config import setup_logger

logger = setup_logger("config_manager")

# Defines the mapping between Streamlit widget keys and their corresponding .env variable names.
# Format: {Streamlit_Key: Env_Variable_Name}
CONFIG_MAP = {
    # GNS3 Server Configuration
    "GNS3_SERVER_HOST": "GNS3_SERVER_HOST",
    "GNS3_SERVER_URL": "GNS3_SERVER_URL",
    "API_VERSION": "API_VERSION",
    "GNS3_SERVER_USERNAME": "GNS3_SERVER_USERNAME",
    "GNS3_SERVER_PASSWORD": "GNS3_SERVER_PASSWORD",
    # Model Configuration
    "MODE_PROVIDER": "MODE_PROVIDER",
    # Note: This key might require special handling (e.g., dynamic loading or mapping)
    "MODEL_NAME": "MODEL_NAME",
    "MODEL_API_KEY": "MODEL_API_KEY",  # Base API Key
    "BASE_URL": "BASE_URL",
    "TEMPERATURE": "TEMPERATURE",
    # Voice Configuration
    "VOICE": "VOICE",
    # Voice TTS Configuration
    "TTS_API_KEY": "TTS_API_KEY",
    "TTS_BASE_URL": "TTS_BASE_URL",
    "TTS_MODEL": "TTS_MODEL",
    "TTS_VOICE": "TTS_VOICE",
    "TTS_SPEED": "TTS_SPEED",
    # Voice STT Configuration
    "STT_API_KEY": "STT_API_KEY",
    "STT_BASE_URL": "STT_BASE_URL",
    "STT_MODEL": "STT_MODEL",
    "STT_LANGUAGE": "STT_LANGUAGE",
    "STT_TEMPERATURE": "STT_TEMPERATURE",
    "STT_RESPONSE_FORMAT": "STT_RESPONSE_FORMAT",
    # Other Settings
    "LINUX_TELNET_USERNAME": "LINUX_TELNET_USERNAME",
    "LINUX_TELNET_PASSWORD": "LINUX_TELNET_PASSWORD",
    # Prompt Configuration
    "ENGLISH_LEVEL": "ENGLISH_LEVEL",
}

# Example list of supported providers (used for validation during loading)
MODEL_PROVIDERS = [
    "openai",
    "anthropic",
    "azure_openai",
    "deepseek",
    "xai",
    "openrouter",
    # ... other providers
]

# Voice TTS configuration options (used for validation during loading)
TTS_MODELS = ["tts-1", "tts-1-hd", "gpt-4o-mini-tts"]
TTS_VOICES = [
    "alloy",
    "ash",
    "ballad",
    "coral",
    "echo",
    "fable",
    "onyx",
    "nova",
    "sage",
    "shimmer",
    "verse",
]

# Voice STT configuration options (used for validation during loading)
STT_MODELS = ["whisper-1", "gpt-4o-transcribe", "gpt-4o-transcribe-diarize"]
STT_RESPONSE_FORMATS = ["json", "text", "srt", "verbose_json", "vtt", "tsv"]

# .env file path
ENV_FILENAME = ".env"
ENV_FILE_PATH = find_dotenv(usecwd=True)

# If find_dotenv fails to locate the file, or if the file does not exist, attempt to create it.
if not ENV_FILE_PATH or not os.path.exists(ENV_FILE_PATH):
    # Assume the file should be located in the current working directory
    ENV_FILE_PATH = os.path.join(os.getcwd(), ENV_FILENAME)

    # If the file still does not exist, create it
    if not os.path.exists(ENV_FILE_PATH):
        try:
            # Create an empty .env file so that set_key can write to it later
            with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(f"# Configuration file: {ENV_FILENAME}\n")
            logger.info("Created new .env file at: %s", ENV_FILE_PATH)
            st.warning(
                f"**{ENV_FILENAME}** file not found. "
                "A new file has been automatically created in the application root directory. "
                "Please configure below and click Save."
            )
        except Exception as e:
            logger.error("Failed to create %s file: %s", ENV_FILENAME, e)
            st.error(
                f"Failed to create {ENV_FILENAME} file. "
                f"Save function will be disabled. Error: {e}"
            )
            ENV_FILE_PATH = ""


def load_config_from_env() -> None:
    """Load configuration from the .env file and initialize st.session_state."""
    # Only attempt to load if the path is valid and the file exists
    logger.info("Starting to load configuration from .env file")
    if ENV_FILE_PATH and os.path.exists(ENV_FILE_PATH):
        logger.debug("Loading .env file from: %s", ENV_FILE_PATH)
        load_dotenv(ENV_FILE_PATH)
        logger.info("Successfully loaded .env file")
    else:
        logger.warning(".env file not found at: %s", ENV_FILE_PATH)

    # Load environment variables into Streamlit's session state
    for st_key, env_key in CONFIG_MAP.items():
        # Get the value from os.environ; default to an empty string if not found
        env_value = os.getenv(env_key)
        default_value = env_value if env_value is not None else ""

        # Special handling for API_VERSION (kept consistent)
        if st_key == "API_VERSION":
            # Ensure the default value is either "2" or "3"
            default_value = "2" if default_value not in ["2", "3"] else default_value

        # Special handling for MODE_PROVIDER (updated key name)
        if st_key == "MODE_PROVIDER":
            if default_value not in MODEL_PROVIDERS:
                # If the loaded value is not in the supported list,
                # set it to an empty string for the user to select
                logger.warning(
                    "Unsupported MODE_PROVIDER %s, setting to empty", default_value
                )
                default_value = ""

        # Special handling for TEMPERATURE (Ensure default is a number or empty string)
        if st_key == "TEMPERATURE" and not default_value.replace(".", "", 1).isdigit():
            # Provide a reasonable default value if not set or invalid
            logger.debug(
                "Invalid TEMPERATURE value : %s, setting to default '0.0'",
                default_value,
            )
            default_value = "0.0"

        # Special handling for VOICE (boolean)
        if st_key == "VOICE":
            # Ensure default_value is a string before processing
            voice_str = str(default_value).lower().strip()

            if voice_str not in (
                "true",
                "false",
                "1",
                "0",
                "yes",
                "no",
                "on",
                "off",
                "",
            ):
                logger.debug(
                    "Invalid VOICE value: %s, setting to default 'false'", default_value
                )
                voice_str = "false"

            # Directly calculate boolean value and store in session_state
            is_enabled: bool = voice_str in ("true", "1", "yes", "on")
            st.session_state[st_key] = is_enabled

            logger.debug("Loaded config: %s = %s", st_key, is_enabled)
            continue  # Important: Skip this loop after processing boolean type to prevent override by the final generic assignment

        # Special handling for TTS configuration
        if st_key == "TTS_MODEL":
            # Only validate TTS_MODEL when voice features are enabled
            voice_enabled = os.getenv("VOICE", "false").lower() in (
                "true",
                "1",
                "yes",
                "on",
            )
            if voice_enabled and default_value not in TTS_MODELS:
                logger.warning(
                    "Unsupported TTS_MODEL %s, setting to empty", default_value
                )
                default_value = ""

        if st_key == "TTS_VOICE":
            # Only validate TTS_VOICE when voice features are enabled
            voice_enabled = os.getenv("VOICE", "false").lower() in (
                "true",
                "1",
                "yes",
                "on",
            )
            if voice_enabled and default_value not in TTS_VOICES:
                logger.warning(
                    "Unsupported TTS_VOICE %s, setting to empty", default_value
                )
                default_value = ""

        if st_key == "TTS_SPEED":
            try:
                speed_float = float(default_value)
                if not (0.25 <= speed_float <= 4.0):
                    logger.debug(
                        "Invalid TTS_SPEED value: %s, setting to default '1.0'",
                        default_value,
                    )
                    default_value = "1.0"
            except ValueError:
                logger.debug(
                    "Invalid TTS_SPEED value: %s, setting to default '1.0'",
                    default_value,
                )
                default_value = "1.0"

        # Special handling for STT configuration
        if st_key == "STT_MODEL":
            # Only validate STT_MODEL when voice features are enabled
            voice_enabled = os.getenv("VOICE", "false").lower() in (
                "true",
                "1",
                "yes",
                "on",
            )
            if voice_enabled and default_value not in STT_MODELS:
                logger.warning(
                    "Unsupported STT_MODEL %s, setting to empty", default_value
                )
                default_value = ""

        if st_key == "STT_RESPONSE_FORMAT":
            # Only validate STT_RESPONSE_FORMAT when voice features are enabled
            voice_enabled = os.getenv("VOICE", "false").lower() in (
                "true",
                "1",
                "yes",
                "on",
            )
            if voice_enabled and default_value not in STT_RESPONSE_FORMATS:
                logger.warning(
                    "Unsupported STT_RESPONSE_FORMAT %s, setting to empty",
                    default_value,
                )
                default_value = ""

        if st_key == "STT_TEMPERATURE":
            try:
                temp_float = float(default_value)
                if not (0.0 <= temp_float <= 1.0):
                    logger.debug(
                        "Invalid STT_TEMPERATURE value: %s, setting to default '0.0'",
                        default_value,
                    )
                    default_value = "0.0"
            except ValueError:
                logger.debug(
                    "Invalid STT_TEMPERATURE value: %s, setting to default '0.0'",
                    default_value,
                )
                default_value = "0.0"

        # Set the value in session state
        st.session_state[st_key] = default_value
        logger.debug(
            "Loaded config: %s = %s",
            st_key,
            "[HIDDEN]" if "PASSWORD" in st_key or "KEY" in st_key else default_value,
        )
    logger.info("Configuration loading completed")


def save_config_to_env() -> None:
    """Save the current session state to the .env file."""
    # Prevent saving if the .env file path is invalid
    logger.info("Starting to save configuration to .env file")

    # Initialize saved_count counter
    saved_count = 0

    if not ENV_FILE_PATH:
        logger.error("Cannot save configuration: .env file path is invalid")
        st.error("Cannot save configuration because the .env file path is invalid.")
        return

    for st_key, env_key in CONFIG_MAP.items():
        current_value = st.session_state.get(st_key)

        if current_value is not None:
            str_value = str(current_value)

            try:
                # Save the value back to the .env file
                set_key(ENV_FILE_PATH, env_key, str_value)

                # Immediately update the current Python process's environment variables
                os.environ[env_key] = str_value

                saved_count += 1
                logger.debug(
                    "Saved config: %s = %s",
                    st_key,
                    "[HIDDEN]"
                    if "PASSWORD" in st_key or "KEY" in st_key
                    else str_value,
                )
            except Exception as e:
                logger.error("Failed to save %s: %s", st_key, e)

    logger.info(
        "Configuration save completed. Saved %s configuration items to %s",
        saved_count,
        ENV_FILE_PATH,
    )
    st.success("Configuration successfully saved to the .env file!")
    st.rerun()
