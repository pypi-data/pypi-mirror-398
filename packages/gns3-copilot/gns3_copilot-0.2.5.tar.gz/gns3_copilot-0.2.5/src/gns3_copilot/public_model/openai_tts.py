"""
OpenAI TTS Interface Module
---------------------------
This module provides a robust interface for converting text to speech using
OpenAI-compatible APIs, specifically optimized for WAV output and automated
duration calculation.
"""

import io
import os
import wave
from typing import Any

from dotenv import load_dotenv
from openai import (
    OpenAI,
)

from gns3_copilot.log_config import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("openai_tts")


def get_tts_config() -> dict[str, Any]:
    """
    Get TTS configuration from environment variables with sensible defaults.
    """
    return {
        "api_key": os.getenv("TTS_API_KEY", "dummy-key"),
        "base_url": os.getenv("TTS_BASE_URL", "http://localhost:4123/v1"),
        "model": os.getenv("TTS_MODEL", "tts-1"),
        "voice": os.getenv("TTS_VOICE", "alloy"),
        "speed": float(os.getenv("TTS_SPEED", "1.0")),
    }


def text_to_speech_wav(
    text: str,
    model: str | None = None,
    voice: str | None = None,
    speed: float | None = None,
    instructions: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> bytes:
    """
    Convert text to speech audio in WAV format using OpenAI TTS API.
    """
    config = get_tts_config()

    # Ensure variable types are determined to avoid issues with Optional
    final_model: str = model if model is not None else str(config["model"])
    final_voice: Any = (
        voice if voice is not None else config["voice"]
    )  # voice SDK type is complex, temporarily using Any or str
    final_speed: float = speed if speed is not None else float(config["speed"])
    final_api_key: str = api_key if api_key is not None else str(config["api_key"])
    final_base_url: str = base_url if base_url is not None else str(config["base_url"])

    if not text or not text.strip():
        raise ValueError("Error: Text content cannot be empty.")

    if len(text) > 4096:
        raise ValueError(
            f"Error: Text length ({len(text)}) exceeds 4096 character limit."
        )

    if not (0.25 <= final_speed <= 4.0):
        raise ValueError("Error: Speed must be between 0.25 and 4.0.")

    # Validate model
    valid_models = ["tts-1", "tts-1-hd", "gpt-4o-mini-tts"]
    if final_model not in valid_models:
        raise ValueError(f"Error: Unsupported model '{final_model}'.")

    try:
        client = OpenAI(api_key=final_api_key, base_url=final_base_url)
        logger.info(f"Generating TTS: model={final_model}, voice={final_voice}")

        # Explicit parameter passing, not using dictionary unpacking (**api_params)
        # This allows Mypy to directly check types, resolving many [arg-type] errors

        # Note: response_format must be a literal supported by the SDK
        response = client.audio.speech.create(
            model=final_model,
            voice=final_voice,
            input=text,
            speed=final_speed,
            response_format="wav",  # Explicit string
        )

        return response.content

    except Exception as e:
        logger.error(f"TTS processing failed: {e}")
        raise Exception(f"TTS Error: {str(e)}") from e


def get_duration(audio_bytes: bytes) -> float:
    """
    Calculate the duration of WAV audio data in seconds using Python's built-in wave module.
    """
    try:
        # Wrap the byte stream in a BytesIO object to make it readable like a file
        with io.BytesIO(audio_bytes) as bio:
            with wave.open(bio, "rb") as wav_f:
                # Get frame count and frame rate (sample rate)
                n_frames = wav_f.getnframes()
                frame_rate = wav_f.getframerate()

                if frame_rate <= 0:
                    return 0.0

                duration = n_frames / float(frame_rate)
                return float(duration)
    except Exception as e:
        logger.error(f"Failed to calculate duration: {e}")
        return 0.0


# --- Usage Example ---
if __name__ == "__main__":
    test_topology = (
        "Network Setup: Router 1 connects to Router 2 via Gigabit interface. "
        "The topology is now ready for OSPF configuration."
    )

    try:
        logger.info("Starting TTS test with default configuration")
        print("Generating audio...")
        print("Using environment variables for TTS configuration...")

        # Display current configuration
        config = get_tts_config()
        logger.info(
            f"TTS Configuration - Model: {config['model']}, Voice: {config['voice']}, Speed: {config['speed']}"
        )
        print(f"TTS Model: {config['model']}")
        print(f"TTS Voice: {config['voice']}")
        print(f"TTS Speed: {config['speed']}")
        print(f"TTS Base URL: {config['base_url']}")
        print(
            f"TTS API Key: {'***' if config['api_key'] != 'dummy-key' else 'dummy-key'}"
        )

        # Generate audio using environment variables (no explicit parameters needed)
        audio_data = text_to_speech_wav(
            text=test_topology
            # All other parameters will be loaded from .env file
        )

        duration = get_duration(audio_data)
        logger.info(
            f"TTS audio generated successfully, duration: {duration:.2f} seconds"
        )
        print(f"Success! Audio Duration: {duration:.2f} seconds")

        with open("network_info.wav", "wb") as f:
            f.write(audio_data)
        logger.info("Audio file saved as network_info.wav")
        print("File saved as network_info.wav")

        # Example with explicit parameter override
        print("\n--- Example with parameter override ---")
        logger.info("Testing TTS with parameter override")
        audio_data_override = text_to_speech_wav(
            text=test_topology,
            voice="onyx",  # Override voice from environment
            api_key="your-api-key",  # Override API key
            base_url="http://localhost:4123/v1",  # Override base URL
        )
        logger.info("Parameter override test completed successfully")
        print("Override example completed successfully!")

    except Exception as err:
        logger.error(f"TTS test process failed: {err}")
        print(f"Process failed: {err}")
