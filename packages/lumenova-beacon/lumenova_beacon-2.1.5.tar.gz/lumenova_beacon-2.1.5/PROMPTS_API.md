# Prompt Management API Reference

## Overview

The Beacon SDK provides comprehensive prompt management with both async and sync methods.

**Pattern:**
- Sync methods (simple names): `Prompt.method(...)` or `prompt.method(...)`
- Async methods ('a' prefix): `await Prompt.amethod(...)` or `await prompt.amethod(...)`

**Important:** You must initialize a `BeaconClient` before using prompt methods, as prompts use the active client for transport configuration.

```python
from lumenova_beacon import BeaconClient
from lumenova_beacon.prompts import Prompt

# Initialize client (required)
client = BeaconClient()

# Now you can use Prompt methods
prompt = await Prompt.aget("Customer Greeting")
```

## Prompt Class Methods

### Fetching Prompts

#### `Prompt.get()` / `Prompt.aget()`
Fetch a prompt by name, ID, label, or version.

```python
# Sync (simple name)
prompt = Prompt.get("Customer Greeting")
prompt = Prompt.get("Customer Greeting", label="production")
prompt = Prompt.get("Customer Greeting", version=3)
prompt = Prompt.get(prompt_id="uuid-here")

# Async ('a' prefix)
prompt = await Prompt.aget("Customer Greeting")
prompt = await Prompt.aget("Customer Greeting", label="production")
```

**Parameters:**
- `name: str` - Prompt name (can contain spaces and special characters)
- `label: str` - Optional label (default: "latest")
- `version: int` - Optional specific version number
- `prompt_id: str` - Optional UUID to fetch by ID instead of name

**Returns:** `Prompt` object

**Raises:**
- `PromptNotFoundError` - Prompt doesn't exist
- `PromptNetworkError` - Network error after retries

---

#### `Prompt.list()` / `Prompt.alist()`
List and search prompts.

```python
# Sync (simple name)
prompts = Prompt.list()
prompts = Prompt.list(tags=["customer-support"])
prompts = Prompt.list(search="greeting", page=1, page_size=20)

# Async ('a' prefix)
prompts = await Prompt.alist()
prompts = await Prompt.alist(tags=["support"])
```

**Parameters:**
- `tags: list[str]` - Filter by tags
- `search: str` - Search query
- `page: int` - Page number (default: 1)
- `page_size: int` - Items per page (default: 10)

**Returns:** `list[Prompt]`

---

### Creating Prompts

#### `Prompt.create()` / `Prompt.acreate()`
Create a new prompt (text or chat).

```python
# Sync (simple name) - Text prompt
prompt = Prompt.create(
    name="Welcome Email",
    template="Hi {{name}}! Welcome to {{app}}.",
    description="Welcome message for new users",
    tags=["email", "onboarding"],
    message="Initial version"  # commit message
)

# Async ('a' prefix) - Chat prompt
prompt = await Prompt.acreate(
    name="Support Bot",
    messages=[
        {"role": "system", "content": "You are helpful for {{product}}."},
        {"role": "user", "content": "{{question}}"}
    ],
    description="Customer support bot",
    tags=["support"],
    message="Initial version"
)

# Sync - Quick example
prompt = Prompt.create(
    name="Quick Prompt",
    template="Hello {{name}}!"
)
```

**Parameters:**
- `name: str` - Prompt name (required)
- `template: str` - For text prompts (Jinja2 template)
- `messages: list[dict]` - For chat prompts (array of role/content)
- `description: str` - Optional description
- `tags: list[str]` - Optional tags
- `message: str` - Optional commit message

**Returns:** `Prompt` object

**Raises:**
- `PromptValidationError` - Invalid content structure
- `PromptNetworkError` - Network error after retries

**Note:** Provide either `template` OR `messages`, not both.

---

### Managing Prompts

#### `prompt.update()` / `prompt.aupdate()`
Update prompt metadata (not content - use `publish()` for that).

```python
# Sync (simple name)
prompt.update(
    name="Updated Name",
    description="Updated description",
    tags=["new", "tags"]
)

# Async ('a' prefix)
await prompt.aupdate(
    name="New Name"
)
```

**Parameters:**
- `name: str` - Optional new name
- `description: str` - Optional new description
- `tags: list[str]` - Optional new tags

**Returns:** `None`

---

#### `prompt.delete()` / `prompt.adelete()`
Delete a prompt (soft delete).

```python
# Sync (simple name)
prompt.delete()

# Async ('a' prefix)
await prompt.adelete()
```

**Returns:** `None`

---

### Versioning

#### `prompt.publish()` / `prompt.apublish()`
Publish a new version of a prompt.

```python
# Sync (simple name) - Text prompt
version = prompt.publish(
    template="Updated: Hello {{name}}!",
    message="Made greeting friendlier"  # commit message
)

# Async ('a' prefix) - Chat prompt
version = await prompt.apublish(
    messages=[
        {"role": "system", "content": "Updated system message"},
        {"role": "user", "content": "{{input}}"}
    ],
    message="Improved system prompt"
)

# Sync - Quick example
version = prompt.publish(
    template="New template",
    message="v2"
)
```

**Parameters:**
- `template: str` - For text prompts
- `messages: list[dict]` - For chat prompts
- `message: str` - Optional commit message

**Returns:** `Prompt` object with new version

---

#### `prompt.set_label()` / `prompt.aset_label()`
Create or update a label pointing to a specific version.

```python
# Sync (simple name)
prompt.set_label(label="production", version=2)
prompt.set_label(label="staging")  # defaults to latest

# Async ('a' prefix)
await prompt.aset_label(label="production", version=2)
```

**Parameters:**
- `label: str` - Label name (e.g., "production", "staging", "latest")
- `version: int` - Optional version number (default: latest version)

**Returns:** `None`

---

## Prompt Instance

The `Prompt` object is returned by `Prompt.get()` and `Prompt.create()`.

### Properties

```python
prompt.id              # UUID
prompt.name            # Prompt name
prompt.description     # Description
prompt.type            # PromptType enum (use .value for 'text' or 'chat' string)
prompt.version         # Current version number
prompt.labels          # List of labels: ["production", "staging"]
prompt.tags            # List of tags
prompt.created_at      # ISO datetime string
prompt.updated_at      # ISO datetime string
prompt.commit_message  # Commit message for current version

# Content properties
prompt.template     # For text prompts: Jinja2 template string (raises ValueError for chat prompts)
prompt.messages     # For chat prompts: list of message dicts (raises ValueError for text prompts)
```

### Methods

#### `format(**kwargs)`
Render the prompt with variables (convenience method).

This is an alias for `compile()` with keyword arguments. Automatically links the prompt to the current active span for tracing.

```python
# Text prompt
message = prompt.format(name="Alice", company="Acme")
# Returns: "Hello Alice! Welcome to Acme."

# Chat prompt
messages = prompt.format(product="CloudSync", question="How to sync?")
# Returns: [
#   {"role": "system", "content": "You are helpful for CloudSync."},
#   {"role": "user", "content": "How to sync?"}
# ]
```

**Parameters:** Keyword arguments matching template variables

**Returns:**
- `str` for text prompts
- `list[dict]` for chat prompts

**Raises:** `PromptCompilationError` if variables are missing

---

#### `compile(variables, auto_link=True)`
Render the prompt with variable substitution.

Uses Jinja2-style `{{variable}}` syntax. By default, automatically links this prompt to the current active span (if one exists) by setting prompt metadata attributes.

```python
# Basic usage (auto-links to current span)
variables = {"name": "Bob", "company": "TechCorp"}
message = prompt.compile(variables)

# Disable auto-linking
message = prompt.compile(variables, auto_link=False)
```

**Parameters:**
- `variables: dict[str, Any]` - Dictionary of variables to substitute
- `auto_link: bool` - If True, automatically link to current span (default: True)

**Returns:**
- `str` for text prompts
- `list[dict]` for chat prompts

**Raises:** `PromptCompilationError` if rendering fails or variables are missing

**Note:** `format(**kwargs)` is a convenience wrapper that calls `compile(kwargs)`

---

#### `link_to_span(span=None)`
Manually link this prompt to a Beacon span.

Sets prompt metadata (id, name, version, labels, tags) as attributes on the specified span. Useful for manual control when you need to link a prompt without calling `compile()` or when `auto_link` is disabled.

```python
from lumenova_beacon import observe

@observe()
def generate_text():
    prompt = Prompt.get("greeting")
    prompt.link_to_span()  # Manually link to current span
    # ... use prompt without compile()
    return result

# Or link to specific span
span = Span(name="my-operation")
span.start()
prompt.link_to_span(span)
```

**Parameters:**
- `span: Span | None` - Span to attach metadata to (default: current span from context)

**Returns:** `None`

---

#### `to_template()`
Convert Jinja2 template to Python f-string format.

Converts `{{variable}}` to `{variable}` for use with Python f-strings. Works for both TEXT and CHAT prompts.

```python
# Text prompt
template = prompt.to_template()
# Input:  "Hello {{name}}!"
# Output: "Hello {name}!"

# Use with f-strings
name = "Bob"
message = eval(f'f"{template}"')

# Chat prompt
messages = prompt.to_template()
# Input:  [{"role": "system", "content": "You are {{role}}"}]
# Output: [{"role": "system", "content": "You are {role}"}]
```

**Returns:**
- `str` - Python-compatible template string (for TEXT prompts)
- `list[dict]` - List of messages with converted templates (for CHAT prompts)

---

#### `to_langchain()`
Convert to LangChain PromptTemplate or ChatPromptTemplate.

```python
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# Text prompt → PromptTemplate
lc_prompt = prompt.to_langchain()
result = lc_prompt.format(name="Charlie")

# Chat prompt → ChatPromptTemplate
lc_chat = prompt.to_langchain()
messages = lc_chat.format_messages(question="How to login?")
```

**Returns:**
- `PromptTemplate` for text prompts
- `ChatPromptTemplate` for chat prompts

**Requires:** `langchain-core>=0.3.0`

---

## Exceptions

### `PromptError`
Base exception for all prompt-related errors.

### `PromptNotFoundError`
Raised when a prompt is not found by name, ID, version, or label.

```python
try:
    prompt = await Prompt.aget("Non Existent")
except PromptNotFoundError as e:
    print(f"Not found: {e}")
```

### `PromptValidationError`
Raised when prompt validation fails (422 error).

```python
try:
    prompt = await Prompt.acreate(
        name="Bad",
        template="text",
        messages=[...]  # Can't have both!
    )
except PromptValidationError as e:
    print(f"Invalid: {e}")
```

### `PromptCompilationError`
Raised when template rendering fails (missing variables, syntax errors).

```python
try:
    message = prompt.format(name="Alice")  # Missing 'company' variable
except PromptCompilationError as e:
    print(f"Compilation failed: {e}")
```

### `PromptNetworkError`
Raised when network request fails after retries.

```python
try:
    prompt = await Prompt.aget("My Prompt")
except PromptNetworkError as e:
    print(f"Network error: {e}")
```

---

## Retry Behavior

All network operations automatically retry on failure:

- **Max retries:** 3
- **Backoff strategy:** Exponential (2^n seconds)
- **Retries on:** Network errors, 5xx errors, timeouts
- **No retry on:** 4xx errors (except 429 rate limit)

---

## Complete Example

```python
import asyncio
from lumenova_beacon import BeaconClient
from lumenova_beacon.prompts import Prompt
from lumenova_beacon.exceptions import PromptNotFoundError

async def main():
    # Initialize client (required for transport configuration)
    client = BeaconClient(api_key="your-api-key")

    # 1. Create prompt
    prompt = await Prompt.acreate(
        name="Welcome Email",
        template="Hi {{name}}! Welcome to {{app}}.",
        tags=["email"],
        message="Initial version"
    )

    # 2. Label as staging
    await prompt.aset_label("staging")

    # 3. Test
    staging = await Prompt.aget("Welcome Email", label="staging")
    email = staging.format(name="Alice", app="MyApp")
    print(email)  # "Hi Alice! Welcome to MyApp."

    # 4. Publish v2
    await prompt.apublish(
        template="Hello {{name}}! Welcome to {{app}}. Get started at {{url}}.",
        message="Added onboarding URL"
    )

    # 5. Promote to production
    await prompt.aset_label("production", version=2)

    # 6. Use in production
    prod = await Prompt.aget("Welcome Email", label="production")
    email = prod.format(name="Bob", app="MyApp", url="https://myapp.com/start")
    print(email)

asyncio.run(main())
```

---

## Sync Example

```python
from lumenova_beacon import BeaconClient
from lumenova_beacon.prompts import Prompt

# Initialize client (required)
client = BeaconClient(api_key="your-api-key")

# Create
prompt = Prompt.create(
    name="Quick Greeting",
    template="Hello {{name}}!"
)

# Fetch
prompt = Prompt.get("Quick Greeting")

# Format
message = prompt.format(name="Charlie")
print(message)  # "Hello Charlie!"
```
