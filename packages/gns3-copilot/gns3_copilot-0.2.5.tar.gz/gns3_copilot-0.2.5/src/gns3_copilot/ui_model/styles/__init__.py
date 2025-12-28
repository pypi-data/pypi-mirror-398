"""CSS styles management module."""

from pathlib import Path


def get_styles() -> str:
    """Read and return all CSS styles wrapped in style tags.

    Returns:
        str: CSS content from main.css file wrapped in <style> tags,
             or empty string if file doesn't exist.
    """
    css_file = Path(__file__).parent / "main.css"
    if css_file.exists():
        css_content = css_file.read_text(encoding="utf-8")
        return f"<style>{css_content}</style>"
    return ""
