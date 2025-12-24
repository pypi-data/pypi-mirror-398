"""This example demonstrates automatic Google Gemini API tracing using OTLP ingestion endpoint.

After calling GoogleGenAIInstrumentor().instrument(), all Gemini API calls are automatically traced
and sent to the OTLP endpoint with full input/output content capture.

Requirements:
    pip install lumenova-beacon[opentelemetry,examples]

Environment Variables:
    BEACON_ENDPOINT=http://localhost:8000  # Your Beacon API endpoint
    BEACON_API_KEY=lum_prod_...            # Your Beacon API key
    BEACON_SESSION_ID=your-session-id      # Optional: Session ID for spans
    GOOGLE_API_KEY=your-google-api-key     # Your Google AI API key

    # Optional: Disable content capture for privacy (enabled by default)
    OPENINFERENCE_HIDE_INPUTS=true
    OPENINFERENCE_HIDE_OUTPUTS=true
"""

import os
import dotenv
from opentelemetry import trace
from google import genai
from google.genai import types
from lumenova_beacon import BeaconClient

dotenv.load_dotenv()

# Initialize BeaconClient with OTLP configuration
client = BeaconClient()

# === Step 1: Instrument Google GenAI ===
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

GoogleGenAIInstrumentor().instrument()

# === Step 2: Use Google Gemini ===
gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model_name = "gemini-2.5-flash"


# === Example 1: Simple Content Generation ===
response = gemini_client.models.generate_content(
    model=model_name,
    contents="What is the capital of France? Answer in one sentence."
)
print(f"Response: {response.text}")
print(f"Tokens: {response.usage_metadata.prompt_token_count} input, {response.usage_metadata.candidates_token_count} output")


# === Example 2: Multi-turn Conversation ===
chat = gemini_client.chats.create(model=model_name)

response1 = chat.send_message("What's the tallest mountain in the world?")
print(f"Chat response 1: {response1.text}")

response2 = chat.send_message("How tall is it in meters?")
print(f"Chat response 2: {response2.text}")


# === Example 3: System Instructions ===
response = gemini_client.models.generate_content(
    model=model_name,
    contents="Write a haiku about coding.",
    config=types.GenerateContentConfig(
        system_instruction="You are a creative poet who writes concise, meaningful verses.",
        temperature=0.9,
        top_p=0.95,
        max_output_tokens=100
    )
)
print(f"Haiku: {response.text}")


# === Example 4: Manual Parent Spans ===
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("research_task") as parent_span:
    parent_span.set_attribute("topic", "quantum computing")

    response1 = gemini_client.models.generate_content(
        model=model_name,
        contents="Explain quantum computing in 2 sentences."
    )
    response2 = gemini_client.models.generate_content(
        model=model_name,
        contents="Name 3 applications of quantum computing."
    )

    parent_span.set_attribute("responses_count", 2)
    print(f"Quantum explanation: {response1.text}")
    print(f"Applications: {response2.text}")


# === Example 5: Streaming Responses ===
print("Streaming response: ", end="")
for chunk in gemini_client.models.generate_content_stream(
    model=model_name,
    contents="Write a one-sentence story about a robot."
):
    if chunk.text:
        print(chunk.text, end="", flush=True)
print("\n")


# Shutdown the tracer provider to flush any remaining spans
provider = trace.get_tracer_provider()
if hasattr(provider, 'shutdown'):
    provider.shutdown()

# All Gemini API calls are automatically traced and sent to the Beacon OTLP endpoint.
# Traces include content generation, chat, streaming, and all parameters.