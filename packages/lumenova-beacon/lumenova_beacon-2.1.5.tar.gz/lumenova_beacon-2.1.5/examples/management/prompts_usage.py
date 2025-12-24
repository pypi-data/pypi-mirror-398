"""Prompts Usage Examples

This example demonstrates prompt management: fetching, formatting, creating,
versioning, labels, and LangChain integration.

Prompts can be TEXT (single template) or CHAT (array of messages).
Use labels like 'production' and 'staging' for deployment workflows.

Requirements:
    pip install lumenova-beacon

    Set environment variables:
    export BEACON_ENDPOINT=https://your-endpoint.com
    export BEACON_API_KEY=your_api_key

    Optional for LangChain:
    pip install lumenova-beacon[langchain]
"""

from lumenova_beacon import BeaconClient
from lumenova_beacon.prompts import Prompt

# Initialize the client (reads from BEACON_ENDPOINT and BEACON_API_KEY env vars)
client = BeaconClient()


# === List Prompts ===
# List all prompts with pagination
prompts = Prompt.list(page=1, page_size=20)
print(f"Total prompts: {len(prompts)}")

for p in prompts:
    print(f"  - {p.name} (v{p.version}, type: {p.type})")


# === Search Prompts ===
# Search by name or description
results = Prompt.list(search="greeting")
print(f"\nPrompts matching 'greeting': {len(results)}")

# Filter by tags
tagged = Prompt.list(tags=["customer-support"])
print(f"Prompts with 'customer-support' tag: {len(tagged)}")


# === Get Prompt by Name ===
# Gets the latest version by default
if prompts:
    prompt = Prompt.get(name=prompts[0].name) # Prompt.get(prompts[0].id) also works
    print(f"\nPrompt: {prompt.name}")
    print(f"  Version: {prompt.version}")
    print(f"  Type: {prompt.type}")
    print(f"  Labels: {prompt.labels}")
    if prompt.description:
        print(f"  Description: {prompt.description}")


# === Get Prompt with Label ===
# Fetch a specific labeled version (production, staging, etc.)
prompt = Prompt.get(name="Customer Greeting", label="production")
print(f"Production version: v{prompt.version}")


# === Get Specific Version ===
# Fetch a specific version number
prompt = Prompt.get(name="Customer Greeting", version=3)
print(f"Version 3: {prompt.template}")


# === Get Prompt by ID ===
# Fetch by UUID
prompt = Prompt.get(prompt_id="550e8400-e29b-41d4-a716-446655440000")


# === Format Text Prompt ===
# Format a TEXT prompt with variables
# Template example: "Hello {{name}}! Welcome to {{company}}."
if prompts:
    prompt = prompts[0]
    if prompt.type == "text" and prompt.template:
        # Format replaces {{var}} with values
        message = prompt.format(name="Alice", company="Acme Corp")
        print(f"\nFormatted text: {message}")


# === Format Chat Prompt ===
# Format a CHAT prompt - returns list of messages
# Messages example: [{"role": "system", "content": "You help with {{product}}"}]
if prompts:
    for p in prompts:
        if p.type == "chat" and p.messages:
            messages = p.format(product="CloudSync", question="How do I sync?")
            print(f"\nFormatted chat ({len(messages)} messages):")
            for msg in messages:
                role = msg.get("role", "") if isinstance(msg, dict) else ""
                content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
                print(f"  {role}: {content[:50]}...")
            break


# === Access Raw Template ===
# Get the raw Jinja2 template with {{var}} syntax
if prompts and prompts[0].type == "text":
    template = prompts[0].template
    print(f"\nRaw template: {template}")


# === Access Raw Messages ===
# Get the raw messages array from chat prompts
if prompts:
    for p in prompts:
        if p.type == "chat" and p.messages:
            print(f"\nRaw messages: {len(p.messages)} messages")
            break


# === Convert to Python Template ===
# Convert {{var}} to {var} for use with f-strings or .format()
if prompts and prompts[0].template:
    template = prompts[0].to_template()
    print(f"\nPython template: {template}")
    # Can use with: template.format(name="Bob", company="Tech")


# === LangChain Integration ===
# Convert to LangChain PromptTemplate or ChatPromptTemplate
try:
    if prompts:
        prompt = prompts[0]
        lc_prompt = prompt.to_langchain()
        print(f"\nLangChain prompt type: {type(lc_prompt).__name__}")

        # Use with LangChain
        # result = lc_prompt.format(name="Eve", company="Future Tech")

        # Or in a chain:
        # from langchain_openai import ChatOpenAI
        # llm = ChatOpenAI(model="gpt-4")
        # chain = lc_prompt | llm
        # response = chain.invoke({"name": "Eve", "company": "Tech"})

except ImportError:
    print("\nLangChain not installed. Run: pip install langchain-core")


# === Create Text Prompt ===
text_prompt = Prompt.create(
    name="Welcome Email",
    template="Hi {{name}}! Welcome to {{app}}. Get started at {{url}}.",
    description="Welcome email for new users",
    tags=["email", "onboarding"],
    message="Initial welcome template",  # commit message
)
print(f"\nCreated text prompt: {text_prompt.name} (ID: {text_prompt.id})")


# === Create Chat Prompt ===
chat_prompt = Prompt.create(
    name="Sales Assistant",
    messages=[
        {"role": "system", "content": "You are a sales assistant for {{company}}."},
        {"role": "user", "content": "{{inquiry}}"},
    ],
    description="AI sales assistant",
    tags=["sales", "chat"],
    message="Initial version",
)
print(f"Created chat prompt: {chat_prompt.name} (type: {chat_prompt.type})")


# === Update Prompt Metadata ===
# Update name, description, or tags (not content - use publish for that)
text_prompt.update(
    name="Welcome Email v2",
    description="Updated welcome email",
    tags=["email", "onboarding", "v2"],
)
print(f"\nUpdated prompt: {text_prompt.name}")


# === Publish New Version ===
# Create a new version with updated content
new_version = text_prompt.publish(
    template="Hello {{name}}! Welcome to {{app}}. Your dashboard: {{url}}.",
    message="Improved greeting and added dashboard link",
)
print(f"Published version {new_version.version}")


# === Set Labels ===
# Label versions for deployment workflows (staging, production, etc.)

# Set staging label on version 1
text_prompt.set_label("staging", version=1)
print("\nSet 'staging' label on version 1")

# After testing, promote to production
text_prompt.set_label("production", version=1)
print("Set 'production' label on version 1")

# Set staging on latest version (no version = latest)
text_prompt.set_label("staging")
print(f"Set 'staging' label on latest version ({new_version.version})")


# === Fetch by Label ===
# Now you can fetch specific labeled versions
staging = Prompt.get(name=text_prompt.name, label="staging")
production = Prompt.get(name=text_prompt.name, label="production")
print(f"\nStaging version: v{staging.version}")
print(f"Production version: v{production.version}")


# === Delete Label ===
# Remove a label from a prompt (note: 'latest' cannot be deleted)
text_prompt.delete_label("staging")
print("\nDeleted 'staging' label")


# === Delete Prompt ===
# Soft delete a prompt
text_prompt.delete()
chat_prompt.delete()
print("\nDeleted prompts")
