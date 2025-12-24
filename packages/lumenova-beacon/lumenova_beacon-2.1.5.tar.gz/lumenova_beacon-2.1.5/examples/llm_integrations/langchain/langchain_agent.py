"""This example demonstrates tracing a LangGraph agent using BeaconCallbackHandler.

LangGraph graphs are automatically detected and traced with span.type = "agent".

Requirements:
    pip install lumenova-beacon[langchain]
    pip install langchain-openai langgraph
"""

from typing import Annotated, TypedDict, Sequence
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from lumenova_beacon import trace, BeaconCallbackHandler

import dotenv

dotenv.load_dotenv()

# Initialize handler with custom metadata
# These attributes will be added to ALL spans created by this handler
# Uses OpenTelemetry semantic conventions for GenAI
handler = BeaconCallbackHandler(
    environment="development",
    agent_name="weather-agent",
    agent_id="weather-agent-001",
    agent_description="A weather assistant that provides forecasts",
    metadata={
        "app_name": "weather-demo",
        "version": "1.0.0",
    }
)


# Define tools
@tool
@trace
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    # Simulated weather data
    weather_data = {
        "new york": "Sunny, 72°F",
        "london": "Cloudy, 61°F",
        "tokyo": "Rainy, 68°F",
        "paris": "Partly cloudy, 65°F",
        "san francisco": "Foggy, 58°F",
        "miami": "Hot and humid, 85°F"
    }
    return weather_data.get(location.lower(), f"Weather data not available for {location}")

@tool
@trace
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Example: '2 + 2' or '10 * 5'"""
    try:
        # Safe evaluation with limited scope
        result = eval(expression, {"__builtins__": {}}, {})
        return f"The result is: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"

@tool
@trace
def search_web(query: str) -> str:
    """Search the web for information about a topic."""
    # Simulated search results
    responses = {
        "python": "Python is a high-level programming language known for its simplicity and readability.",
        "ai": "Artificial Intelligence refers to computer systems that can perform tasks requiring human intelligence.",
        "langgraph": "LangGraph is a library for building stateful, multi-actor applications with LLMs."
    }
    for key, value in responses.items():
        if key in query.lower():
            return value
    return f"Search results for '{query}': General information available online."

# Define the agent state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Create the tools list
tools = [get_weather, calculator, search_web]
tool_node = ToolNode(tools)

# Initialize the LLM with tools
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState):
    """Call the LLM with tool binding."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    """Determine if we should continue to tools or end."""
    last_message = state["messages"][-1]
    
    # If the last message has tool calls, route to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Otherwise, end
    return END

# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set entry point
workflow.set_entry_point("agent")

# Add edges
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# After tools, always go back to agent
workflow.add_edge("tools", "agent")

# Compile the graph
app = workflow.compile()


# === Execute Agent ===
if __name__ == "__main__":
    # Multi-step reasoning query that requires multiple tool calls
    query = "What's the weather in London and calculate 100 / 4"
    print(f"Query: {query}")

    result = app.invoke(
        {"messages": [HumanMessage(content=query)]},
        config={'callbacks': [handler]},
    )

    print(f"Response: {result['messages'][-1].content}")

# Check your Beacon dashboard to see:
# - Parent span with span.type = "agent" (LangGraph automatically detected)
# - Child "agent" and "tools" node spans with span.type = "chain"
# - Individual tool execution spans (get_weather, calculator)
# - Complete trace hierarchy showing agentic reasoning flow
#
# Custom metadata on all spans (using OTEL semantic conventions):
# - deployment.environment.name = "development"
# - gen_ai.agent.name = "weather-agent"
# - gen_ai.agent.id = "weather-agent-001"
# - gen_ai.agent.description = "A weather assistant that provides forecasts"
# - beacon.metadata.app_name = "weather-demo"
# - beacon.metadata.version = "1.0.0"
#
# LLM spans will also include auto-extracted model parameters:
# - gen_ai.request.temperature
# - gen_ai.request.top_p
# - gen_ai.request.max_tokens
