"""
Public module for parsing tool execution results

This module is specifically designed to parse and format results returned by tools_v2
after tool execution, supporting multiple formats and providing unified error handling.
Mainly used for result display in UI interfaces.

Supported formats:
- JSON strings
- Python literal strings
- Dictionary objects
- List objects (JSON arrays)
- Primitive types (int, float, bool, str)
- Error message strings
- Plain text output

Author: Guobin Yue
"""

import ast
import json
from typing import Any

from gns3_copilot.log_config import setup_tool_logger

logger = setup_tool_logger("parse_tool_content")


def parse_tool_content(
    content: str | dict | list | int | float | bool | None,
    fallback_to_raw: bool = True,
    strict_mode: bool = False,
) -> dict[str, Any] | list[Any] | Any:
    """
    Parse tool execution results into structured data, specifically for UI display.

    This function can handle various input types including strings, dictionaries, lists,
    and primitive types. It ensures the returned data can be properly serialized
    by json.dumps.

    Args:
        content: Content returned by tools (can be str, dict, list, int, float, bool, or None)
        fallback_to_raw: Whether to return raw content when parsing fails, default True
        strict_mode: Strict mode, raises exceptions when parsing fails, default False

    Returns:
        Union[Dict[str, Any], List[Any], Any]: Parsed data that can be serialized by json.dumps:
        - Successfully parsed JSON/Python literal data
        - Original dict/list objects (passed through)
        - Primitive types (int, float, bool, str)
        - {"raw": content} when unable to parse but fallback_to_raw=True
        - {"error": "error_message"} when parsing fails and fallback_to_raw=False
        - {} for None input

    Raises:
        ValueError: When strict_mode=True and parsing fails
        TypeError: When content type is unsupported and strict_mode=True

    Examples:
        >>> parse_tool_content('{"status": "success", "data": [1, 2, 3]}')
        {'status': 'success', 'data': [1, 2, 3]}

        >>> parse_tool_content({"status": "success"})
        {'status': 'success'}

        >>> parse_tool_content([1, 2, 3])
        [1, 2, 3]

        >>> parse_tool_content(42)
        42

        >>> parse_tool_content("{'name': 'PC1', 'status': 'ok'}")
        {'name': 'PC1', 'status': 'ok'}

        >>> parse_tool_content("Invalid JSON input: ...")
        {'raw': 'Invalid JSON input: ...'}

        >>> parse_tool_content("{}")
        {}

        >>> parse_tool_content(None)
        {}
    """
    # Handle None input
    if content is None:
        logger.debug("Content is None, returning empty dict")
        return {}

    # Handle dictionary objects (already parsed)
    if isinstance(content, dict):
        logger.debug("Content is already a dictionary, returning as-is")
        return content

    # Handle list objects (JSON arrays)
    if isinstance(content, list):
        logger.debug("Content is already a list, returning as-is")
        return content

    # Handle primitive types that are JSON serializable
    if isinstance(content, (str, int, float, bool)):
        # For strings, we need to try parsing them
        if isinstance(content, str):
            # Empty string handling
            if not content.strip():
                logger.debug("Content is empty or whitespace, returning empty dict")
                return {}

            s = content.strip()

            # Handle empty dictionary case
            if s == "{}":
                logger.debug("Content is empty dictionary, returning empty dict")
                return {}

            logger.debug(
                "Attempting to parse string content: %s %s",
                s[:100],
                "..." if len(s) > 100 else "",
            )

            # Try to parse as Python literal
            # (higher priority as many tools return Python format strings)
            try:
                result = ast.literal_eval(s)
                logger.debug("Successfully parsed as Python literal")
                return result
            except (ValueError, SyntaxError) as e:
                logger.debug("Failed to parse as Python literal: %s", e)

            # Try to parse as JSON
            try:
                result = json.loads(s)
                logger.debug("Successfully parsed as JSON")
                return result
            except json.JSONDecodeError as e:
                logger.debug("Failed to parse as JSON: %s", e)

            # Handle parsing failure for strings
            error_msg = "Unable to parse content as JSON or Python literal"
            logger.warning(
                "%s: %s %s", error_msg, s[:100], "..." if len(s) > 100 else ""
            )

            if strict_mode:
                raise ValueError("%s. Content: %s", error_msg, s)

            if fallback_to_raw:
                logger.debug("Returning raw content as fallback")
                return {"raw": s}
            return {"error": error_msg}
        # For non-string primitives (int, float, bool), return as-is
        logger.debug(
            "Content is a primitive type %s, returning as-is", type(content).__name__
        )
        return content

    # Handle unsupported types
    error_msg = (  # type: ignore[unreachable]
        "Content must be str, dict, list, int, float, bool, or None, got "
        f"{type(content).__name__}"
    )
    logger.error(error_msg)

    if strict_mode:
        raise TypeError(error_msg)

    if fallback_to_raw:
        logger.debug("Returning raw content as fallback")
        return {"raw": str(content)}
    return {"error": error_msg}


def format_tool_response(
    content: str | dict | list | int | float | bool | None, indent: int = 2
) -> str:
    """
    Format tool response as a beautiful JSON string for UI display.

    This function ensures that the output is always a valid JSON string that can be
    properly displayed in UI interfaces.

    Args:
        content: Content returned by tools (can be str, dict, list, int, float, bool, or None)
        indent: JSON indentation spaces, default 2

    Returns:
        str: Formatted JSON string, always valid JSON
    """
    try:
        parsed = parse_tool_content(content, fallback_to_raw=True, strict_mode=False)
        # Ensure the result can be serialized to JSON
        return json.dumps(parsed, ensure_ascii=False, indent=indent)
    except (TypeError, ValueError) as e:
        # If the parsed result cannot be serialized, convert to string and wrap
        logger.error("Cannot serialize parsed result to JSON: %s", e)
        try:
            return json.dumps({"raw": str(content)}, ensure_ascii=False, indent=indent)
        except Exception:
            # Last resort: return a simple error message
            return json.dumps(
                {"error": "Unable to format response"},
                ensure_ascii=False,
                indent=indent,
            )
    except Exception as e:
        logger.error("Error formatting tool response: %s", e)
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=indent)


# Test function to verify the implementation
def _test_parse_tool_content() -> None:
    """Test function to verify parse_tool_content works correctly with all input types"""
    test_cases: list[tuple[Any, Any]] = [
        # String inputs
        (
            '{"status": "success", "data": [1, 2, 3]}',
            {"status": "success", "data": [1, 2, 3]},
        ),
        ("{'name': 'PC1', 'status': 'ok'}", {"name": "PC1", "status": "ok"}),
        ("[1, 2, 3]", [1, 2, 3]),
        ('"hello"', "hello"),
        ("42", 42),
        ("true", True),
        ("3.14", 3.14),
        ("{}", {}),
        ("  {}  ", {}),
        ("", {}),
        ("   ", {}),
        ("Invalid JSON input", {"raw": "Invalid JSON input"}),
        # Direct object inputs
        ({"status": "success"}, {"status": "success"}),
        ([1, 2, 3], [1, 2, 3]),
        ("hello", "hello"),
        (42, 42),
        (True, True),
        (3.14, 3.14),
        (None, {}),
    ]

    print("Testing parse_tool_content function:")
    for i, (input_data, expected) in enumerate(test_cases):
        result = parse_tool_content(input_data)
        status = "✓" if result == expected else "✗"
        print(f"Test {i + 1}: {status} Input: {repr(input_data)} -> {result}")

    print("\nTesting format_tool_response function:")
    format_tests = [
        '{"status": "success"}',
        "{}",
        None,
        "Invalid input",
        {"direct": "dict"},
        [1, 2, 3],
        42,
        True,
    ]

    for i, input_data in enumerate(format_tests):
        result = format_tool_response(input_data)
        # Verify it's valid JSON
        try:
            json.loads(result)
            valid = "✓"
        except Exception:
            valid = "✗"
        print(f"Format Test {i + 1}: {valid} Input: {repr(input_data)} -> {result}")


if __name__ == "__main__":
    _test_parse_tool_content()
