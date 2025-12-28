import io
import os
from typing import IO, Any, BinaryIO, Literal, cast

from dotenv import load_dotenv
from openai import OpenAI
from openai._types import NOT_GIVEN

from gns3_copilot.log_config import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger("openai_stt")

DEFAULT_GNS3_PROMPT = (
    "GNS3, Cisco, router, switch, OSPF, BGP, EIGRP, ISIS, VLAN, STP, "
    "interface, FastEthernet, GigabitEthernet, loopback, config terminal, "
    "no shutdown, show running-config, Wireshark, encapsulation."
)


def get_stt_config() -> dict[str, Any]:
    """
    Get STT configuration from environment variables with sensible defaults.
    """
    return {
        "api_key": os.getenv("STT_API_KEY", ""),
        "base_url": os.getenv("STT_BASE_URL", "http://127.0.0.1:8001/v1"),
        "model": os.getenv("STT_MODEL", "whisper-1"),
        "language": os.getenv("STT_LANGUAGE", None),
        "temperature": float(os.getenv("STT_TEMPERATURE", "0.0")),
        "response_format": os.getenv("STT_RESPONSE_FORMAT", "json"),
    }


def speech_to_text(
    audio_data: bytes | BinaryIO,
    model: str | None = None,
    language: str | None = None,
    prompt: str | None = DEFAULT_GNS3_PROMPT,
    response_format: str | None = None,
    temperature: float | None = None,
    timestamp_granularities: list[Literal["word", "segment"]] | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str | dict[str, Any]:
    """
    Transcribe audio to text using OpenAI Whisper API.
    """
    config = get_stt_config()

    # Determine specific type to avoid Optional
    f_model: str = model if model is not None else str(config["model"])
    f_response_format: Any = (
        response_format if response_format is not None else config["response_format"]
    )
    f_temperature: float = (
        temperature if temperature is not None else float(config["temperature"])
    )
    f_api_key: str = api_key if api_key is not None else str(config["api_key"])
    f_base_url: str = base_url if base_url is not None else str(config["base_url"])
    f_language: str | None = (
        language if language is not None else config.get("language")
    )

    if not audio_data:
        raise ValueError("Audio data cannot be empty")

    # Use IO[bytes] to unify type declarations for BytesIO and BinaryIO
    audio_file: IO[bytes]
    file_name: str = "audio.wav"

    if isinstance(audio_data, bytes):
        size_mb = len(audio_data) / (1024 * 1024)
        audio_file = io.BytesIO(audio_data)

    else:
        audio_file = audio_data
        file_name = getattr(audio_file, "name", "audio.wav")

        audio_file.seek(0, os.SEEK_END)
        size_mb = audio_file.tell() / (1024 * 1024)
        audio_file.seek(0)

    if size_mb > 25:
        raise ValueError(f"Audio file size too large ({size_mb:.2f}MB).")

    try:
        client = OpenAI(
            api_key=f_api_key if f_api_key else "local-dummy",
            base_url=f_base_url,
            timeout=60.0,
        )

        response = client.audio.transcriptions.create(
            file=(file_name, audio_file),
            model=f_model,
            language=cast(Any, f_language or NOT_GIVEN),
            prompt=cast(Any, prompt or NOT_GIVEN),
            response_format=f_response_format,
            temperature=f_temperature,
            timestamp_granularities=cast(Any, timestamp_granularities or NOT_GIVEN),
        )

        # Explicitly handle response type to resolve unreachable and no-any-return
        if isinstance(response, str):
            return response

        # For Pydantic model objects
        if hasattr(response, "model_dump"):
            data = cast(dict[str, Any], response.model_dump())
            if f_response_format == "json":
                return str(data.get("text", ""))
            return data

        return str(response)

    except Exception as e:
        logger.error(f"STT API call failed: {type(e).__name__} - {str(e)}")
        raise Exception(f"Speech-to-text service error: {str(e)}") from e


def speech_to_text_simple(audio_data: bytes | BinaryIO, **kwargs: Any) -> str:
    """
    Simplified version that always returns a plain transcription string.
    """
    result = speech_to_text(audio_data=audio_data, response_format="text", **kwargs)
    return str(result)


# Module Test
if __name__ == "__main__":
    print("Whisper STT module initialized...")

    # Display current environment configuration
    print("\n=== Current STT Environment Configuration ===")
    config = get_stt_config()
    for key, value in config.items():
        if "key" in key.lower() and value:
            print(f"{key}: ***")
        else:
            print(f"{key}: {value}")

    # Example usage with environment variables
    print("\n=== Example Usage ===")
    print("Using environment variables for configuration:")
    print("result = speech_to_text(audio_data)")
    print()
    print("Overriding specific parameters:")
    print(
        "result = speech_to_text(audio_data, model='gpt-4o-transcribe', language='en')"
    )
