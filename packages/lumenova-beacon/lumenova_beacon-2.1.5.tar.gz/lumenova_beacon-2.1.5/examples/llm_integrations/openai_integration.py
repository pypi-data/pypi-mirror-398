"""This example demonstrates automatic OpenAI API tracing using OpenTelemetry OpenAIInstrumentor.

After calling OpenAIInstrumentor().instrument(), all OpenAI API calls are automatically traced.

Requirements:
    pip install lumenova-beacon[opentelemetry,examples]
    Set OPENAI_API_KEY environment variable
"""

import os
import asyncio
import dotenv
from openai import OpenAI, AsyncOpenAI
from lumenova_beacon import BeaconClient

dotenv.load_dotenv()

beacon_client = BeaconClient()

# === Step 1: Instrument OpenAI ===
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

OpenAIInstrumentor().instrument()


# === Step 2: Use OpenAI Normally ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model_name = "gpt-4o-mini"


# === Example 1: Simple Chat Completion ===
response = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France? Answer in one sentence."}
    ]
)
print(f"Response: {response.choices[0].message.content}")
print(f"Tokens: {response.usage.prompt_tokens} input, {response.usage.completion_tokens} output")


# === Example 2: Streaming Responses ===
stream = client.chat.completions.create(
    model=model_name,
    messages=[{"role": "user", "content": "Write a haiku about coding."}],
    stream=True
)

haiku = ""
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        haiku += content
        print(content, end="", flush=True)
print("\n")


# === Example 3: Function Calling ===
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City and state, e.g., San Francisco, CA"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model=model_name,
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools
)

print("Tools called by GPT:")
for tool_call in response.choices[0].message.tool_calls or []:
    print(f"  - {tool_call.function.name}: {tool_call.function.arguments}")


# === Example 4: Multi-turn Conversation ===
messages = [
    {"role": "user", "content": "What's the tallest mountain in the world?"},
    {"role": "assistant", "content": "Mount Everest is the tallest mountain in the world."},
    {"role": "user", "content": "How tall is it?"}
]

response = client.chat.completions.create(model=model_name, messages=messages)
print(f"Multi-turn response: {response.choices[0].message.content}")


# === Example 5: Manual Parent Spans using SDK ===
with beacon_client.trace("research_task") as span:
    span.set_attribute("topic", "quantum computing")

    response1 = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": "Explain quantum computing in 2 sentences."}]
    )
    response2 = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": "Name 3 applications of quantum computing."}]
    )

    span.set_attribute("responses_count", 2)
    print(f"Quantum explanation: {response1.choices[0].message.content}")
    print(f"Applications: {response2.choices[0].message.content}")


# === Example 6: Vision - Image Understanding ===
response = client.chat.completions.create(
    model=model_name,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image? Be concise."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/320px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                    }
                }
            ]
        }
    ],
    max_tokens=300
)
print(f"Image description: {response.choices[0].message.content}")


# === Example 7: Async Operations ===
async def async_examples():
    """Async operations."""
    async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = await async_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": "Explain async programming in Python in 2 sentences."}]
    )
    print(f"Async response: {response.choices[0].message.content}")

    questions = [
        "What is the capital of Japan?",
        "What is the largest ocean?",
        "What is the speed of light?"
    ]

    tasks = [
        async_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": q}]
        )
        for q in questions
    ]

    responses = await asyncio.gather(*tasks)
    print(f"Completed {len(responses)} concurrent async requests")


asyncio.run(async_examples())


# === Example 8: Advanced Parameters ===
response = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "system", "content": "You are a creative storyteller."},
        {"role": "user", "content": "Write a one-sentence story about a robot."}
    ],
    temperature=0.9,
    top_p=0.95,
    max_tokens=100,
    presence_penalty=0.5,
    frequency_penalty=0.5
)
print(f"Creative response: {response.choices[0].message.content}")

# All OpenAI API calls are automatically traced including chat completions, streaming,
# function calling, vision, async operations, and all parameters.
