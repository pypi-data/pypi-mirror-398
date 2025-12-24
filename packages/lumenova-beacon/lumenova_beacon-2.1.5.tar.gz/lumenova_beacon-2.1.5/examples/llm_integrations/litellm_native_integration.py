"""LiteLLM Native Integration with Beacon.

BeaconClient automatically instruments LiteLLM for seamless tracing.

Requirements:
    pip install lumenova-beacon litellm python-dotenv

Setup:
    ENDPOINT=your-endpoint
    API_KEY=your-key
    API_VERSION=your-api-version
    DEPLOYMENT=gpt-4o-mini
"""

import asyncio
import dotenv
from lumenova_beacon import BeaconClient
import litellm

dotenv.load_dotenv()

# Initialize BeaconClient with LiteLLM auto-instrumentation enabled
# Note: Set auto_instrument_litellm=True to automatically set up LiteLLM tracing
# Do NOT use LiteLLMInstrumentor() alongside this - it would create duplicate spans
beacon_client = BeaconClient(auto_instrument_litellm=True)

# Configure
PROVIDER = 'provider-name'
DEPLOYMENT = 'gpt-4o-mini'
ENDPOINT = 'your-endpoint'
API_KEY = 'your-api-key'
API_VERSION = '2024-02-15-preview'

if not ENDPOINT or not API_KEY:
    print("Error: ENDPOINT and API_KEY must be set")
    exit(1)

MODEL_NAME = f"{PROVIDER}/{DEPLOYMENT}"

# === Example 1: Simple Completion ===
try:
    response = litellm.completion(
        model=MODEL_NAME,
        api_base=ENDPOINT,
        api_key=API_KEY,
        api_version=API_VERSION,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France? One sentence."}
        ],
        temperature=0
    )
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens: {response.usage.prompt_tokens} input, {response.usage.completion_tokens} output\n")
except Exception:
    pass

# === Example 2: Custom Metadata ===
try:
    response = litellm.completion(
        model=MODEL_NAME,
        api_base=ENDPOINT,
        api_key=API_KEY,
        api_version=API_VERSION,
        messages=[
            {"role": "user", "content": "Name 3 European capitals. Be brief."}
        ],
        metadata={
            "generation_name": "european_capitals",
            "session_id": "user-session-123",
            "user_id": "user-456",
            "tags": ["geography", "education"],
            "custom_field": "example_value"
        }
    )
    print(f"Response: {response.choices[0].message.content}\n")
except Exception:
    pass

# === Example 3: Streaming ===
try:
    print("Streaming: ", end="")
    response = litellm.completion(
        model=MODEL_NAME,
        api_base=ENDPOINT,
        api_key=API_KEY,
        api_version=API_VERSION,
        messages=[
            {"role": "user", "content": "Write a haiku about technology. Be brief."}
        ],
        stream=True,
        metadata={"generation_name": "haiku_stream"}
    )
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n")
except Exception:
    pass

# === Example 4: Tool Calling ===
try:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    response = litellm.completion(
        model=MODEL_NAME,
        api_base=ENDPOINT,
        api_key=API_KEY,
        api_version=API_VERSION,
        messages=[
            {"role": "user", "content": "What's the weather in Tokyo?"}
        ],
        tools=tools,
        tool_choice="auto",
        metadata={"generation_name": "weather_tool_call"}
    )

    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            print(f"Tool called: {tool_call.function.name}")
            print(f"Arguments: {tool_call.function.arguments}\n")
    else:
        print(f"Response: {response.choices[0].message.content}\n")
except Exception:
    pass

# === Example 5: Multi-Turn Conversation ===
try:
    conversation = [
        {"role": "user", "content": "What's the tallest mountain?"},
        {"role": "assistant", "content": "Mount Everest is the tallest mountain."},
        {"role": "user", "content": "How tall is it in meters?"}
    ]

    response = litellm.completion(
        model=MODEL_NAME,
        api_base=ENDPOINT,
        api_key=API_KEY,
        api_version=API_VERSION,
        messages=conversation,
        metadata={
            "generation_name": "mountain_conversation",
            "trace_id": "conv-trace-123"
        }
    )
    print(f"Response: {response.choices[0].message.content}\n")
except Exception:
    pass

# === Example 6: Async Operations ===
async def async_examples():
    """Demonstrate async LiteLLM calls."""
    try:
        # Single async call
        response = await litellm.acompletion(
            model=MODEL_NAME,
            api_base=ENDPOINT,
            api_key=API_KEY,
            api_version=API_VERSION,
            messages=[
                {"role": "user", "content": "Explain async programming in 2 sentences."}
            ],
            metadata={"generation_name": "async_example"}
        )
        print(f"Async response: {response.choices[0].message.content}\n")
    except Exception:
        pass

    try:
        # Concurrent async calls
        questions = [
            "What is the capital of Japan?",
            "What is the largest ocean?",
            "What is the speed of light?"
        ]

        tasks = [
            litellm.acompletion(
                model=MODEL_NAME,
                api_base=ENDPOINT,
                api_key=API_KEY,
                api_version=API_VERSION,
                messages=[{"role": "user", "content": q}],
                max_tokens=50,
                metadata={"generation_name": f"concurrent_q{i+1}"}
            )
            for i, q in enumerate(questions)
        ]

        responses = await asyncio.gather(*tasks)

        for question, response in zip(questions, responses):
            print(f"Q: {question}")
            print(f"A: {response.choices[0].message.content}")
        print()
    except Exception:
        pass

asyncio.run(async_examples())

# === Example 7: Error Handling ===
try:
    response = litellm.completion(
        model="azure/invalid-deployment",
        api_base=ENDPOINT,
        api_key=API_KEY,
        api_version=API_VERSION,
        messages=[{"role": "user", "content": "Hello"}],
        metadata={"generation_name": "error_example"}
    )
except Exception as e:
    print(f"Error: {type(e).__name__}")
    print(f"Message: {str(e)[:80]}...\n")

# All LiteLLM operations are automatically traced to Beacon
