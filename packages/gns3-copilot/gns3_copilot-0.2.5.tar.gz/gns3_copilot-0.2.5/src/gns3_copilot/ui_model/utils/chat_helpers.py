"""
Chat Helper Functions for GNS3 Copilot.

This module provides helper functions for the chat interface, including
message rendering, project selection UI, and chat stream processing.

Functions:
    list_thread_ids: Get all unique thread IDs from checkpoint database.
    create_session_options: Create session selection options for sidebar.
    format_unique_title: Format a unique title with thread ID prefix.
    extract_message_text: Extract text from AIMessage content.
    render_message_history: Render historical messages from state.
    render_project_card: Render a single project selection card.
    render_project_selection_ui: Render project selection interface.
    handle_text_message: Handle text streaming from AIMessage.
    handle_tool_call_start: Handle the start of a tool call.
    handle_tool_call_chunk: Handle streaming tool call chunks.
    handle_tool_call_complete: Handle completion of a tool call.
    handle_tool_response: Handle tool message response.
    process_chat_stream: Process the chat stream and handle UI updates.
"""

import json
from typing import Any

import streamlit as st
from langchain.messages import AIMessage, HumanMessage, ToolMessage

from gns3_copilot.public_model import (
    format_tool_response,
    get_duration,
    text_to_speech_wav,
)

# Configuration constants
MAX_ITERATIONS = 50
RECURSION_LIMIT = 28
SESSION_TITLE_PREFIX_LENGTH = 6


def list_thread_ids(checkpointer: Any) -> list[str]:
    """
    Get all unique thread IDs from LangGraph checkpoint database.

    Args:
        checkpointer: LangGraph checkpointer instance.

    Returns:
        List of unique thread IDs ordered by most recent activity.
        Returns empty list on error or if table doesn't exist.
    """
    try:
        res = checkpointer.conn.execute(
            "SELECT DISTINCT thread_id FROM checkpoints ORDER BY rowid DESC"
        ).fetchall()
        return [r[0] for r in res]
    except Exception:
        # Table might not exist yet, return empty list
        return []


def create_session_options(
    checkpointer: Any, thread_ids: list[str]
) -> list[tuple[str, str | None]]:
    """
    Create session selection options for the sidebar.

    Args:
        checkpointer: LangGraph checkpointer instance.
        thread_ids: List of thread IDs to create options for.

    Returns:
        List of (title, thread_id) tuples. First element is a placeholder.
    """
    options: list[tuple[str, str | None]] = [("(Please select session)", None)]

    for thread_id in thread_ids:
        checkpoint = checkpointer.get({"configurable": {"thread_id": thread_id}})
        title = (
            checkpoint.get("channel_values", {}).get("conversation_title")
            if checkpoint
            else None
        ) or "New Session"
        # Use part of thread_id to avoid same title name issues
        unique_title = format_unique_title(title, thread_id)
        options.append((unique_title, thread_id))

    return options


def format_unique_title(title: str, thread_id: str) -> str:
    """
    Format a unique title with thread ID prefix.

    Args:
        title: The original title.
        thread_id: The thread ID to use for uniqueness.

    Returns:
        Formatted unique title with thread ID prefix.
    """
    return f"{title} ({thread_id[:SESSION_TITLE_PREFIX_LENGTH]})"


def extract_message_text(content: Any) -> str:
    """
    Extract text from AIMessage content, handling both string and list formats.

    Args:
        content: The AIMessage content (can be str or list for Gemini).

    Returns:
        Extracted text as string.
    """
    if (
        isinstance(content, list)
        and content
        and isinstance(content[0], dict)
        and "text" in content[0]
    ):
        return str(content[0]["text"])
    return str(content) if isinstance(content, str) else ""


def render_message_history(messages: list) -> None:
    """
    Render historical messages from state history.

    Args:
        messages: List of message objects to render.
    """
    current_assistant_block = None

    for message_object in messages:
        if isinstance(message_object, HumanMessage):
            # Close any open assistant chat message block
            if current_assistant_block is not None:
                current_assistant_block.__exit__(None, None, None)
                current_assistant_block = None

            with st.chat_message("user"):
                st.markdown(message_object.content)

        elif isinstance(message_object, (AIMessage, ToolMessage)):
            # Open a new assistant chat message block if none is open
            if current_assistant_block is None:
                current_assistant_block = st.chat_message("assistant")
                current_assistant_block.__enter__()

            if isinstance(message_object, AIMessage):
                # Render AIMessage content
                text = extract_message_text(message_object.content)
                if text:
                    st.markdown(text)

                # Render tool calls
                if (
                    isinstance(message_object.tool_calls, list)
                    and message_object.tool_calls
                ):
                    for tool in message_object.tool_calls:
                        tool_id = tool.get("id", "UNKNOWN_ID")
                        tool_name = tool.get("name", "UNKNOWN_TOOL")
                        tool_args = tool.get("args", {})
                        with st.expander(
                            f"**Tool Call:** {tool_name} `call_id: {tool_id}`",
                            expanded=False,
                        ):
                            st.json(
                                {
                                    "name": tool_name,
                                    "id": tool_id,
                                    "args": tool_args,
                                    "type": "tool_call",
                                },
                                expanded=True,
                            )

            if isinstance(message_object, ToolMessage):
                content_pretty = format_tool_response(message_object.content)
                with st.expander(
                    f"**Tool Response** `call_id: {message_object.tool_call_id}`",
                    expanded=False,
                ):
                    st.json(json.loads(content_pretty), expanded=2)

    # Close any remaining open assistant chat message block
    if current_assistant_block is not None:
        current_assistant_block.__exit__(None, None, None)


def render_project_card(project: tuple, col: Any, agent: Any, config: dict) -> None:
    """
    Render a single project selection card.

    Args:
        project: Project tuple (name, id, device_count, link_count, status).
        col: Streamlit column to render in.
        agent: The agent instance for state updates.
        config: Configuration dictionary for agent.
    """
    name, project_id, device_count, link_count, status = project
    is_opened = status.lower() == "opened"

    with col:
        with st.container(border=True):
            status_icon = "🟢" if is_opened else "⚪"
            st.markdown(f"###### {status_icon} {name}")
            st.caption(f"ID: {project_id[:8]}")
            st.write(f"{device_count} Devices | {link_count} Links")

            if is_opened:
                st.success(f"Status: {status.upper()}")
            else:
                st.warning(f"Status: {status.upper()} (Unavailable)")

            if st.button(
                "Select Project" if is_opened else "Project Closed",
                key=f"btn_{project_id}",
                use_container_width=True,
                disabled=not is_opened,
                type="primary" if is_opened else "secondary",
            ):
                agent.update_state(config, {"selected_project": project})
                st.success(f"Project {name} has been selected!")
                st.rerun()


def render_project_selection_ui(projects: list, agent: Any, config: dict) -> None:
    """
    Render project selection interface cards.

    Args:
        projects: List of project tuples.
        agent: The agent instance for state updates.
        config: Configuration dictionary for agent.
    """
    if projects:
        opened_projects = [p for p in projects if p[4].lower() == "opened"]

        # Auto-select if only one opened project
        if len(opened_projects) == 1:
            project = opened_projects[0]
            agent.update_state(config, {"selected_project": project})
            st.toast(f"Automatically selecting project: {project[0]}")
            st.rerun()

        cols = st.columns([1, 1])
        for index, project in enumerate(projects):
            render_project_card(project, cols[index % 2], agent, config)
    else:
        st.error("No projects found in GNS3.")
        if st.button("Refresh List"):
            st.rerun()


def handle_text_message(
    msg: AIMessage, placeholder: Any, current_text: str
) -> tuple[str, bool]:
    """
    Handle text streaming from AIMessage.

    Args:
        msg: The AIMessage to process.
        placeholder: Streamlit placeholder for text display.
        current_text: Current accumulated text.

    Returns:
        Tuple of (updated_text, should_trigger_tts).
    """
    text = extract_message_text(msg.content)
    if text:
        current_text += text
        placeholder.markdown(current_text, unsafe_allow_html=True)

    should_trigger_tts = bool(
        text
        and (
            msg.tool_calls
            or msg.response_metadata.get("finish_reason") in ["tool_calls", "stop"]
        )
    )
    return current_text, should_trigger_tts


def handle_tool_call_start(msg: AIMessage) -> dict[str, Any] | None:
    """
    Handle the start of a tool call.

    Args:
        msg: The AIMessage to process.

    Returns:
        Tool state dictionary or None if no tool call started.
    """
    if not msg.tool_calls:
        return None

    # Process first tool call (only one at a time)
    tool = msg.tool_calls[0]
    return {
        "id": tool.get("id"),
        "name": tool.get("name", "UNKNOWN_TOOL"),
        "args_string": "",
    }


def handle_tool_call_chunk(msg: AIMessage, tool_state: dict) -> None:
    """
    Handle streaming tool call chunks.

    Args:
        msg: The AIMessage to process.
        tool_state: Current tool state dictionary to update.
    """
    if not hasattr(msg, "tool_call_chunks") or not msg.tool_call_chunks:
        return

    for chunk_update in msg.tool_call_chunks:
        args_chunk = chunk_update.get("args", "")
        if isinstance(args_chunk, str):
            tool_state["args_string"] += args_chunk


def handle_tool_call_complete(msg: AIMessage, tool_state: dict[str, Any]) -> None:
    """
    Handle completion of a tool call and display.

    Args:
        msg: The AIMessage to process.
        tool_state: Tool state dictionary with call info.
    """
    try:
        parsed_args = json.loads(tool_state["args_string"])
    except json.JSONDecodeError:
        parsed_args = {"error": "JSON parse failed after stream complete."}

    # Parse tool_input if present
    try:
        command_list = json.loads(parsed_args["tool_input"])
        parsed_args["tool_input"] = command_list
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    display_tool_call = {
        "name": tool_state["name"],
        "id": tool_state["id"],
        "args": parsed_args,
        "type": tool_state.get("type", "tool_call"),
    }

    with st.expander(
        f"**Tool Call:** {tool_state['name']} `call_id: {tool_state['id']}`",
        expanded=False,
    ):
        st.json(display_tool_call, expanded=False)


def handle_tool_response(
    msg: ToolMessage,
    placeholder: Any,
    audio_bytes: bytes | None,
    voice_enabled: bool,
) -> tuple[bytes | None, str]:
    """
    Handle tool message response.

    Args:
        msg: The ToolMessage to process.
        placeholder: Streamlit placeholder to clear.
        audio_bytes: Current audio bytes if playing.
        voice_enabled: Whether voice TTS is enabled.

    Returns:
        Tuple of (audio_bytes, empty_string for next text chunk).
    """
    from time import sleep

    # Wait for audio playback to complete
    if voice_enabled and audio_bytes:
        sleep(get_duration(audio_bytes))

    content_pretty = format_tool_response(msg.content)
    with st.expander(
        f"**Tool Response** `call_id: {msg.tool_call_id}`",
        expanded=False,
    ):
        st.json(json.loads(content_pretty), expanded=False)

    placeholder.empty()
    return None, ""


def process_chat_stream(
    agent: Any,
    config: dict,
    user_message: str,
    voice_enabled: bool,
) -> None:
    """
    Process the chat stream and handle UI updates.

    Args:
        agent: The LangGraph agent instance.
        config: Configuration dictionary.
        user_message: User's input message.
        voice_enabled: Whether voice TTS is enabled.
    """
    with st.chat_message("assistant"):
        active_text_placeholder = st.empty()
        current_text_chunk = ""
        current_tool_state = None
        tts_played = False
        audio_bytes = None

        for chunk in agent.stream(
            {"messages": [HumanMessage(content=user_message)]},
            config=config,
            stream_mode="messages",
        ):
            for msg in chunk:
                if isinstance(msg, AIMessage):
                    # Handle text streaming
                    current_text_chunk, should_trigger_tts = handle_text_message(
                        msg, active_text_placeholder, current_text_chunk
                    )

                    # Play TTS if text is ending and not yet played
                    if (
                        should_trigger_tts
                        and not tts_played
                        and current_text_chunk.strip()
                        and voice_enabled
                    ):
                        tts_played = True
                        try:
                            with st.spinner("Generating voice..."):
                                audio_bytes = text_to_speech_wav(current_text_chunk)
                                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        except Exception as e:
                            st.error(f"TTS Error: {e}")

                    # Handle tool call start
                    if msg.tool_calls and not current_tool_state:
                        current_tool_state = handle_tool_call_start(msg)

                    # Handle tool call chunks
                    if current_tool_state:
                        handle_tool_call_chunk(msg, current_tool_state)

                    # Handle tool call completion
                    if current_tool_state is not None and (
                        msg.response_metadata.get("finish_reason") == "tool_calls"
                        or (msg.response_metadata.get("finish_reason") == "STOP")
                    ):
                        handle_tool_call_complete(msg, current_tool_state)

                if isinstance(msg, ToolMessage):
                    audio_bytes, current_text_chunk = handle_tool_response(
                        msg, active_text_placeholder, audio_bytes, voice_enabled
                    )
                    current_tool_state = None
                    tts_played = False
