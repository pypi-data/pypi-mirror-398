# mypy: ignore-errors

"""
GNS3 Network Automation Assistant

This module implements an AI-powered assistant for GNS3 network automation and management.
It uses LangChain for agent orchestration and DeepSeek LLM for natural language processing.
The assistant provides comprehensive GNS3 topology management capabilities including:
- Reading and analyzing GNS3 project topologies
- Creating and managing network nodes and links
- Executing network configuration and display commands on multiple devices
- Managing VPCS (Virtual PC Simulator) commands
- Starting and controlling GNS3 nodes

The assistant integrates with various tools to provide a complete network automation
solution for GNS3 environments.
"""

import operator
import os
import sqlite3
from typing import Annotated, Literal

import streamlit as st
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import AnyMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.managed.is_last_step import RemainingSteps
from typing_extensions import TypedDict

from gns3_copilot.gns3_client import GNS3TopologyTool
from gns3_copilot.log_config import setup_logger
from gns3_copilot.prompts import TITLE_PROMPT, load_system_prompt
from gns3_copilot.tools_v2 import (
    ExecuteMultipleDeviceCommands,
    ExecuteMultipleDeviceConfigCommands,
    GNS3CreateNodeTool,
    GNS3LinkTool,
    GNS3StartNodeTool,
    GNS3TemplateTool,
    LinuxTelnetBatchTool,
    VPCSMultiCommands,
)

load_dotenv()

# Set up logger for GNS3 Copilot
logger = setup_logger("gns3_copilot", log_file="log/gns3_copilot.log")

base_model = init_chat_model(
    model_provider=os.getenv("MODE_PROVIDER"),
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("MODEL_API_KEY"),
    base_url=os.getenv("BASE_URL", ""),
    temperature=os.getenv("TEMPERATURE", "0"),
    configurable_fields="any",
    config_prefix="foo",
)

title_mode = base_model
# use OpenRouter
# base_model = init_chat_model(
#    model_provider="openai",
#    base_url = "https://openrouter.ai/api/v1",
#    temperature = 0,
#    api_key = os.getenv("OPENROUTER_API_KEY"),
# model="openai/gpt-4o-mini",
# model="google/gemini-2.5-flash", # It ignores the observations after the tool is executed.
#    model="x-ai/grok-4-fast",
# )
# assist_model = init_chat_model(
#    model="google_genai:gemini-2.5-flash",
#    temperature=1
# )

# Define the available tools for the agent
tools = [
    GNS3TemplateTool(),  # Get GNS3 node templates
    GNS3TopologyTool(),  # Read GNS3 topology information
    GNS3CreateNodeTool(),  # Create new nodes in GNS3
    GNS3LinkTool(),  # Create links between nodes
    GNS3StartNodeTool(),  # Start GNS3 nodes
    ExecuteMultipleDeviceCommands(),  # Execute show/display commands on multiple devices
    ExecuteMultipleDeviceConfigCommands(),  # Execute configuration commands on multiple devices
    VPCSMultiCommands(),  # Execute VPCS commands on multiple devices
    LinuxTelnetBatchTool(),  # Execute Linux commands via Telnet on multiple devices
]
# Augment the LLM with tools
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = base_model.bind_tools(tools)

# Log application startup
logger.info("GNS3 Copilot application starting up")
logger.debug("Available tools: %s", [tool.__class__.__name__ for tool in tools])


# Define state
class MessagesState(TypedDict):
    """
    GNS3 Copilot conversation state management class.

    Maintains the conversation state for the LangGraph workflow, including message history,
    call counters, and session titles for comprehensive dialogue management.

    Attributes:
        messages: List of conversation messages with cumulative updates using operator.add
        llm_calls: Counter for tracking the number of LLM invocations
        remaining_steps: Is automatically managed by LangGraph's RemainingSteps to track and limit recursion depth.
        conversation_title: Optional conversation title for session identification and management
    """

    messages: Annotated[list[AnyMessage], operator.add]

    llm_calls: int

    remaining_steps: RemainingSteps

    # Optional conversation title
    conversation_title: str | None

    # Store the complete tuple selected by the user
    selected_project: tuple[str, str, int, int, str]


# Define llm call  node
def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    current_prompt = load_system_prompt()
    # print(current_prompt)

    # Get the previously stored project tuple
    selected_p = state.get("selected_project")

    # Construct context messages
    context_messages = []
    if selected_p:
        # Convert tuple information to natural language to tell LLM which project user selected
        project_info = (
            "User has selected project: "
            f"Project_Name={selected_p[0]}, "
            f"Project_ID={selected_p[1]}, "
            f"Device_Number={selected_p[2]}, "
            f"Link_Number={selected_p[3]}, "
            f"Status={selected_p[4]}"
        )
        context_messages.append(
            SystemMessage(content=f"Current Context: {project_info}")
        )

    # Merge message lists
    full_messages = (
        [SystemMessage(content=current_prompt)] + context_messages + state["messages"]
    )
    # print(full_messages)
    return {
        "messages": [model_with_tools.invoke(full_messages)],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# Define generate title node
def generate_title(state: MessagesState) -> dict:
    """
    Generate a conversation title using a lightweight assistant LLM (title_model).
    This node is only executed when no title has been set yet (first round only).
    """

    # Only generate a title if it hasn't been set yet
    if state.get("conversation_title") in [None, "New Session"]:
        messages = state["messages"]

        # Build the prompt for title generation
        title_prompt_messages = [
            SystemMessage(content=TITLE_PROMPT),
            messages[0],  # User's first message
            messages[-1],  # Assistant's final response in this turn
        ]
        logger.debug("summary_messages for title generation: %s", title_prompt_messages)

        # Call the title generation model (currently using the same base_model / DeepSeek)
        try:
            response = title_mode.invoke(
                title_prompt_messages, config={"configurable": {"foo_temperature": 1.0}}
            )
            logger.debug("generate_title: %s", response)
            raw_content = response.content
            logger.debug("Raw title output from model: %s", raw_content)

            new_title = raw_content.strip()

            # Safety: truncate long titles and avoid line breaks
            if len(new_title) > 40:  # Increased limit for better Chinese support
                new_title = new_title[:38] + "..."

            # Remove unwanted characters
            new_title = new_title.replace("\n", " ").replace('"', "").replace("'", "")

            if not new_title:
                new_title = "GNS3 Session"

            logger.info("Generated new title: %s", new_title)
            return {"conversation_title": new_title}

        except Exception as e:
            logger.error("Title generation failed: %s", e)
            return {"conversation_title": "Untitled Session"}

    # Title already exists → no update needed
    return {}


# Define tool node
def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


# Routing logic after the LLM node
def should_continue(
    state: MessagesState,
) -> Literal["tool_node", "title_generator_node", END]:
    """
    Determine the next step after the LLM has produced a response.

    - If the LLM requested any tool calls → route to tool_node
    - If this is the first complete turn (llm_calls == 1) and no title exists → generate a title
    - Otherwise → conversation is complete, go to END
    """
    last_message = state["messages"][-1]
    llm_calls = state.get("llm_calls", 0)
    current_title = state.get("conversation_title")

    # LLM requested one or more tool executions
    if last_message.tool_calls:
        logger.debug(
            "LLM requested %s tool call(s) → routing to 'tool_node'",
            len(last_message.tool_calls),
        )
        return "tool_node"

    # First full interaction completed and title not yet generated
    if current_title in [None, "GNS3 Session"]:
        logger.info(
            "First turn finished, no title yet → routing to 'title_generator_node'"
        )
        return "title_generator_node"

    # Normal completion (multi-turn conversation or title already exists)
    logger.debug(
        "Conversation turn complete (llm_calls= %s ) → routing to END", llm_calls
    )
    return END


# Routing logic after the tool node, Check remaining_steps
def recursion_limit_continue(state: MessagesState) -> Literal["llm_call", END]:
    """
    Routing logic after tool execution to prevent infinite recursion.

    Determines whether to continue with another LLM call or end the conversation
    based on remaining steps and message type.

    Args:
        state: Current conversation state with messages and remaining steps

    Returns:
        "llm_call" to continue processing, END to terminate conversation

    Logic:
        - If the last message is ToolMessage and steps >= 4: continue to LLM
        - Otherwise: end the conversation to prevent infinite loops
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, ToolMessage):
        if state["remaining_steps"] < 4:
            return END
        return "llm_call"

    return END


# Build and compile the agent
# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("title_generator_node", generate_title)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
# Conditional routing after LLM response
# Determines the next step based on whether LLM needs to call tools or generate title
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",  # Route to tool execution if LLM requested tools
        "title_generator_node": "title_generator_node",  # Generate title on first interaction
        END: END,  # End conversation if no tools needed
    },
)
# Conditional routing after tool execution
# Prevents infinite recursion by checking remaining steps before continuing
agent_builder.add_conditional_edges(
    "tool_node",
    recursion_limit_continue,
    {
        "llm_call": "llm_call",  # Continue to LLM if tools executed and steps remain
        END: END,  # End conversation to prevent infinite loops
    },
)

agent_builder.add_edge("title_generator_node", END)

# Add checkpointing
LANGGRAPH_DB_PATH = "gns3_langgraph.db"


@st.cache_resource(show_spinner="Initializing conversation persistence...")
def get_checkpointer() -> SqliteSaver:
    """
    Create and cache a single SqliteSaver instance for the entire app lifetime.

    Important notes:
    - `check_same_thread=False` is required because Streamlit runs in a multi-threaded environment.
    - The returned checkpointer is automatically shared across all user sessions.
    """
    conn = sqlite3.connect(LANGGRAPH_DB_PATH, check_same_thread=False)
    # SqliteSaver will create the necessary tables on first use
    return SqliteSaver(conn)


# Compile the agent
@st.cache_resource(show_spinner="Compiling LangGraph agent...")
def get_agent():
    """
    Compile and cache the LangGraph agent.

    The agent builder (`agent_builder`) and checkpointer are defined earlier in the file.
    By not passing them as parameters we avoid Streamlit cache invalidation issues
    when objects are recreated (even if they are logically identical).
    """
    return agent_builder.compile(checkpointer=get_checkpointer())


langgraph_checkpointer = get_checkpointer()  # Cached SqliteSaver instance
agent = get_agent()  # Cached compiled LangGraph agent (with persistence)

# Show the agent
# graph_image_data = agent.get_graph(xray=True).draw_mermaid_png()
# with open("agent_graph.png", "wb") as f:
#    f.write(graph_image_data)
