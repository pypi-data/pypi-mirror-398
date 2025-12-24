"""This example demonstrates a LangGraph with mixed streaming capabilities.

It features two nodes:
1. A streaming node that generates a story.
2. A non-streaming node that summarizes the story.

The entire graph is invoked asynchronously with streaming to show how to handle
mixed output types (streaming chunks vs complete messages).

Requirements:
    pip install lumenova-beacon[langchain]
    pip install langchain-openai langgraph
    Set OPENAI_API_KEY environment variable
"""

import asyncio
import dotenv
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, add_messages

from lumenova_beacon import BeaconCallbackHandler

dotenv.load_dotenv()

# Initialize Beacon handler
handler = BeaconCallbackHandler()

# Define the state
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Node 1: Streaming LLM
async def streaming_story_node(state: GraphState):
    """Generates a story using a streaming LLM."""
    print("\n--- Node 1: Streaming Story ---")
    
    # Initialize streaming LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, streaming=True)
    
    messages = state["messages"]
    # We'll just use the last message as the prompt for the story
    prompt = messages[-1]
    
    response = await llm.ainvoke(
        [prompt],
        # config={"callbacks": [handler]}
    )
    return {"messages": [response]}

# Node 2: Non-streaming LLM
async def non_streaming_summary_node(state: GraphState):
    """Summarizes the story using a non-streaming LLM."""
    print("\n\n--- Node 2: Non-streaming Summary ---")
    
    # Initialize non-streaming LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=False)
    
    messages = state["messages"]
    story = messages[-1].content
    
    prompt = HumanMessage(content=f"Summarize the following story in one sentence:\n\n{story}")
    
    response = await llm.ainvoke(
        [prompt],
        # config={"callbacks": [handler]}
    )
    return {"messages": [response]}

# Build the graph
workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node("story_generator", streaming_story_node)
workflow.add_node("summarizer", non_streaming_summary_node)

# Set entry point
workflow.set_entry_point("story_generator")

# Add edges
workflow.add_edge("story_generator", "summarizer")
workflow.add_edge("summarizer", END)

# Compile the graph
app = workflow.compile()

async def main():
    # Initial input
    inputs = {"messages": [HumanMessage(content="Tell me a short story about a brave toaster.")]}
    
    print("Starting graph execution...")
    
    # Stream the graph execution
    # We use astream to get updates from the graph as it executes
    async for event in app.astream(inputs, config={"callbacks": [handler]}):
        for node_name, output in event.items():
            print(f"\n--- Finished Node: {node_name} ---")
            last_message = output["messages"][-1]
            print(f"Output: {last_message.content[:100]}...")

    print("\nGraph execution complete.")

if __name__ == "__main__":
    asyncio.run(main())
