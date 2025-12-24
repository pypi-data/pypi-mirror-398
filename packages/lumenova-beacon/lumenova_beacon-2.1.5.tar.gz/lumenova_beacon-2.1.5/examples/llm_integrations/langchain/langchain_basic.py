"""This example demonstrates LangChain tracing using BeaconCallbackHandler.

Use request-time callbacks (config={"callbacks": [handler]}) for proper trace hierarchy.

Requirements:
    pip install lumenova-beacon[langchain]
    pip install langchain-openai
"""
from lumenova_beacon import BeaconCallbackHandler

import dotenv

dotenv.load_dotenv()

# Create handler
handler = BeaconCallbackHandler()

# === Example 1: Simple LLM Call ===
try:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Use request-time callbacks (recommended for full trace hierarchy)
    response = llm.invoke(
        "What is the capital of France?",
        config={"callbacks": [handler]}
    )

    print(f"Response: {response.content}")

except ImportError:
    print("⚠ langchain-openai not installed. Install: pip install langchain-openai")


# === Example 2: Chain with Multiple Steps ===
try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    # Create a simple chain (prompt → LLM → parser)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that answers questions concisely."),
        ("user", "{question}")
    ])

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser

    # Invoke with callbacks - traces entire chain including nested operations
    result = chain.invoke(
        {"question": "What is the capital of Spain?"},
        config={"callbacks": [handler]}
    )

    print(f"Result: {result}")

except ImportError:
    print("⚠ langchain-openai not installed. Install: pip install langchain-openai")

# All LangChain operations have been traced and sent to Beacon
# Check your dashboard to see span hierarchy, timing, and LLM details
