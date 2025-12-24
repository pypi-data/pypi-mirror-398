"""Strands SDK Integration with Beacon via OpenTelemetry.

Strands SDK uses OpenTelemetry for telemetry. BeaconClient automatically captures all
Strands spans (agent, tool calls, model invocations) through OpenTelemetry integration.

Key: Initialize BeaconClient BEFORE creating Strands agents.

Requirements:
    pip install lumenova-beacon[opentelemetry] strands python-dotenv

Setup:
    AWS_ACCESS_KEY_ID=your-aws-access-key
    AWS_SECRET_ACCESS_KEY=your-aws-secret-key
    AWS_DEFAULT_REGION=us-east-1
    BEACON_ENDPOINT=http://localhost:8000 (optional)
    BEACON_API_KEY=your-api-key (optional)
"""

import dotenv
from lumenova_beacon import BeaconClient
from strands import Agent
from strands.models.bedrock import BedrockModel

dotenv.load_dotenv()


# === Step 1: Initialize Beacon FIRST ===
beacon_client = BeaconClient()

from strands.telemetry import StrandsTelemetry
# Configure the telemetry
# (Creates new tracer provider and sets it as global)
strands_telemetry = StrandsTelemetry().setup_otlp_exporter()

# === Step 2: Configure Strands Agent ===
model = BedrockModel(
    model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
)

system_prompt = """You are a helpful assistant that provides concise answers to questions."""

agent = Agent(
    model=model,
    system_prompt=system_prompt,
    trace_attributes={
        "session.id": "user-session-123",
        "user.id": "user@example.com",
    }
)

# === Step 3: Use Agent - All Spans Automatically Traced to Beacon ===
try:
    print("Query: What is the capital of France?")
    result = agent("What is the capital of France?")
    print(f"Response: {result.message}\n")
except Exception as e:
    print(f"Error: {e}\n")

# === Example 2: Follow-up Question ===
try:
    print("Query: What's the population?")
    result = agent("What's the population?")
    print(f"Response: {result.message}\n")
except Exception as e:
    print(f"Error: {e}\n")

# All agent interactions, model calls, and tool invocations are automatically
# captured as OpenTelemetry spans and sent to Beacon
