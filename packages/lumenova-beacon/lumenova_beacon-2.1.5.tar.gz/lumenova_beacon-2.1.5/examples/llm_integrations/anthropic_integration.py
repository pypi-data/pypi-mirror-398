"""This example demonstrates automatic Anthropic API tracing using OpenTelemetry AnthropicInstrumentor.

After calling AnthropicInstrumentor().instrument(), all Anthropic API calls are automatically
traced. This pattern works for any OpenTelemetry instrumentor.

Requirements:
    pip install lumenova-beacon[opentelemetry,anthropic,examples]
    Set ANTHROPIC_API_KEY environment variable
"""

import os
import asyncio
import dotenv
from opentelemetry import trace
from lumenova_beacon.core.client import BeaconClient

dotenv.load_dotenv()

beacon_client = BeaconClient()

# === Step 1: Instrument Anthropic ===
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

AnthropicInstrumentor().instrument()


# === Step 2: Use Anthropic Normally ===
from anthropic import Anthropic

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# === Example 1: Simple Message ===
response = anthropic_client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "What is the capital of France? Answer in one sentence."}
    ]
)
print(f"Response: {response.content[0].text}")
print(f"Tokens: {response.usage.input_tokens} input, {response.usage.output_tokens} output")


# === Example 2: Multi-turn Conversation ===
messages = [
    {"role": "user", "content": "What's the tallest mountain in the world?"},
    {"role": "assistant", "content": "Mount Everest is the tallest mountain in the world."},
    {"role": "user", "content": "How tall is it?"}
]

response = anthropic_client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=300,
    messages=messages
)
print(f"Multi-turn response: {response.content[0].text}")


# === Example 3: Manual Parent Spans ===
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("travel_planning") as parent_span:
    parent_span.set_attribute("destination", "Paris")

    response1 = anthropic_client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": "What's the best time to visit Paris?"}]
    )

    response2 = anthropic_client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": "Name 3 must-see attractions in Paris."}]
    )

    parent_span.set_attribute("responses_count", 2)
    print(f"Best time: {response1.content[0].text[:80]}...")
    print(f"Attractions: {response2.content[0].text[:80]}...")


# === Example 4: Streaming Responses ===
with anthropic_client.messages.stream(
    model="claude-opus-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a haiku about programming."}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
print("\n")  # Newline after streaming


# === Example 5: Tool Calling ===
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City and state, e.g., San Francisco, CA"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    },
    {
        "name": "get_time",
        "description": "Get current time for a location",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"]
        }
    }
]

response = anthropic_client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather and time in Tokyo?"}]
)

print("Tools called by Claude:")
for content in response.content:
    if content.type == "tool_use":
        print(f"  - {content.name}: {content.input}")


# === Example 6: Async Operations ===
async def async_examples():
    """Async operations."""
    from anthropic import AsyncAnthropic

    async_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = await async_client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": "Explain async programming in Python in 2 sentences."}]
    )
    print(f"Async response: {response.content[0].text}")

    questions = [
        "What is the capital of Japan?",
        "What is the largest ocean?",
        "What is the speed of light?"
    ]

    tasks = [
        async_client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": q}]
        )
        for q in questions
    ]

    responses = await asyncio.gather(*tasks)
    print(f"Completed {len(responses)} concurrent async requests")


asyncio.run(async_examples())


# === Example 7: System Prompts and Parameters ===
response = anthropic_client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=500,
    temperature=0.7,
    system="You are a helpful assistant that provides concise, factual answers. Always be friendly and professional.",
    messages=[{"role": "user", "content": "Explain quantum computing in 3 sentences."}]
)
print(f"Quantum response: {response.content[0].text}")


provider = trace.get_tracer_provider()
if hasattr(provider, 'shutdown'):
    provider.shutdown()

# All Anthropic API calls are automatically traced including messages, streaming,
# tool calling, async operations, and all parameters.
