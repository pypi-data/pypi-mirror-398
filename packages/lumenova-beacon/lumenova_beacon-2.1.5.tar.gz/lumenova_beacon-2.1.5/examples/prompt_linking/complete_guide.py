"""
Complete Guide to Prompt Linking with Traces

This comprehensive example demonstrates all methods of linking prompts to traces
across different LLM frameworks: OpenAI, Anthropic, LangChain, and LangGraph.

Requirements:
    - lumenova-beacon
    - openai (for OpenAI examples)
    - anthropic (for Anthropic examples)
    - langchain-core, langchain-openai (for LangChain examples)
    - langgraph (for LangGraph examples)

Setup:
    export BEACON_API_KEY=your_api_key
    export OPENAI_API_KEY=your_openai_key
    export ANTHROPIC_API_KEY=your_anthropic_key
"""

import asyncio
import os
from typing import Annotated

from lumenova_beacon import BeaconClient
from lumenova_beacon.prompts import Prompt
from lumenova_beacon import trace

import dotenv
dotenv.load_dotenv()

# ============================================================================
# SETUP
# ============================================================================

# Initialize Beacon client
BeaconClient()

# Initialize LLM clients
try:
    from openai import OpenAI, AsyncOpenAI, AzureOpenAI, AsyncAzureOpenAI

    # openai_client = OpenAI()
    openai_client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    # async_openai_client = AsyncOpenAI()
    async_openai_client = AsyncAzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
except ImportError:
    openai_client = None
    async_openai_client = None
    print("OpenAI not installed. OpenAI examples will be skipped.")

try:
    from anthropic import Anthropic, AsyncAnthropic
    anthropic_client = Anthropic()
    async_anthropic_client = AsyncAnthropic()
except ImportError:
    anthropic_client = None
    async_anthropic_client = None
    print("Anthropic not installed. Anthropic examples will be skipped.")

try:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.output_parsers import StrOutputParser
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    from lumenova_beacon import BeaconCallbackHandler

    beacon_handler = BeaconCallbackHandler()

    chat_open_ai = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    )
except ImportError:
    beacon_handler = None
    print("LangChain not installed. LangChain examples will be skipped.")

try:
    from langgraph.graph import StateGraph, END
    from typing_extensions import TypedDict
except ImportError:
    StateGraph = None
    print("LangGraph not installed. LangGraph examples will be skipped.")


# ============================================================================
# SECTION 1: DIRECT LLM SDK EXAMPLES (OpenAI & Anthropic)
# ============================================================================

# ----------------------------------------------------------------------------
# Example 1.1: Basic Automatic Linking with OpenAI
# ----------------------------------------------------------------------------

def _ensure_messages(compiled: str | list[dict]) -> list[dict]:
    """Convert compiled prompt to messages array if needed."""
    if isinstance(compiled, str):
        return [{"role": "user", "content": compiled}]
    return compiled


# Azure deployment name (use env var for Azure, or model name for OpenAI)
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")


@trace()
async def example_basic_openai_linking():
    """
    Basic automatic prompt linking with OpenAI.

    When you call compile() inside a @trace() function, the prompt metadata
    is automatically linked to the current span.
    """
    # Fetch prompt and compile it
    prompt = await Prompt.aget(name='customer-greeting')
    compiled = prompt.compile({'name': 'Alice', 'company': 'Acme Corp'})
    messages = _ensure_messages(compiled)

    # Use with OpenAI - prompt metadata is automatically captured in trace
    response = openai_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=messages
    )

    return response.choices[0].message.content


# ----------------------------------------------------------------------------
# Example 1.2: Version-Specific Prompts with Labels
# ----------------------------------------------------------------------------

@trace()
async def example_version_specific_prompt():
    """
    Fetch and use a specific version of a prompt using labels.

    Labels like 'production' or 'staging' let you manage different
    versions of prompts across environments.
    """
    # Fetch production version
    prompt = await Prompt.aget(name='customer-greeting', label='production')
    compiled = prompt.compile({'name': 'Bob', 'company': 'TechStart'})
    messages = _ensure_messages(compiled)

    response = openai_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=messages
    )

    return response.choices[0].message.content


# ----------------------------------------------------------------------------
# Example 1.3: Manual Linking with link_to_span()
# ----------------------------------------------------------------------------

@trace()
async def example_manual_linking():
    """
    Manual prompt linking using link_to_span().

    Use this when you need to link a prompt but aren't using compile().
    Useful for custom templating or when you need finer control.
    """
    prompt = await Prompt.aget(name='customer-greeting')

    # Manually link to current span
    prompt.link_to_span()

    # Use template directly (not via compile)
    template = prompt.to_template()

    # Custom processing...
    custom_messages = [
        {'role': 'user', 'content': template.format(name='Charlie', company='StartupCo')}
    ]

    response = openai_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=custom_messages
    )

    return response.choices[0].message.content


# ----------------------------------------------------------------------------
# Example 1.4: Disabling Auto-Linking
# ----------------------------------------------------------------------------

@trace()
async def example_disable_auto_linking():
    """
    Disable automatic linking when you don't want prompt metadata in traces.

    Useful for testing or when you want to control exactly when linking occurs.
    """
    prompt = await Prompt.aget(name='customer-greeting')

    # Compile without auto-linking
    compiled = prompt.compile(
        {'name': 'Diana', 'company': 'Enterprise'},
        auto_link=False  # No automatic span linking
    )
    messages = _ensure_messages(compiled)

    response = openai_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=messages
    )

    return response.choices[0].message.content


# ----------------------------------------------------------------------------
# Example 1.5: Async vs Sync Usage
# ----------------------------------------------------------------------------

@trace()
def example_sync_prompt_usage():
    """
    Synchronous prompt usage with get() and compile().

    Use sync methods when working in non-async contexts.
    """
    # Sync fetch
    prompt = Prompt.get('customer-greeting')

    # Compile works the same way
    compiled = prompt.compile({'name': 'Eve', 'company': 'DataCorp'})
    messages = _ensure_messages(compiled)

    response = openai_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=messages
    )

    return response.choices[0].message.content


# ----------------------------------------------------------------------------
# Example 1.6: Anthropic-Specific Patterns
# ----------------------------------------------------------------------------

@trace()
async def example_anthropic_system_prompt():
    """
    Using prompts with Anthropic's API (system prompts).

    Anthropic requires system messages to be passed separately from messages.
    The compile() method handles this automatically for chat-style prompts.
    """
    prompt = await Prompt.aget(name='customer-greeting')
    compiled = prompt.compile({'name': 'Frank', 'company': 'AI Solutions'})
    messages = _ensure_messages(compiled)

    # Extract system prompt if present
    system_prompt = None
    filtered_messages = []
    for msg in messages:
        if msg['role'] == 'system':
            system_prompt = msg['content']
        else:
            filtered_messages.append(msg)

    # Use with Anthropic
    response = anthropic_client.messages.create(
        model='claude-opus-4-20250514',
        max_tokens=1024,
        system=system_prompt if system_prompt else 'You are a helpful assistant.',
        messages=filtered_messages
    )

    return response.content[0].text


@trace()
async def example_anthropic_streaming():
    """
    Streaming responses with Anthropic.

    Prompt metadata is still captured even with streaming responses.
    """
    prompt = await Prompt.aget(name='customer-greeting')
    compiled = prompt.compile({'name': 'Grace', 'company': 'StreamTech'})
    messages = _ensure_messages(compiled)

    # Extract system prompt
    system_prompt = None
    filtered_messages = []
    for msg in messages:
        if msg['role'] == 'system':
            system_prompt = msg['content']
        else:
            filtered_messages.append(msg)

    # Stream response
    full_response = ""
    with anthropic_client.messages.stream(
        model='claude-opus-4-20250514',
        max_tokens=1024,
        system=system_prompt if system_prompt else 'You are a helpful assistant.',
        messages=filtered_messages
    ) as stream:
        for text in stream.text_stream:
            full_response += text

    return full_response


@trace()
async def example_anthropic_async():
    """
    Async Anthropic client usage.
    """
    prompt = await Prompt.aget(name='customer-greeting')
    compiled = prompt.compile({'name': 'Henry', 'company': 'AsyncCo'})
    messages = _ensure_messages(compiled)

    # Extract system prompt
    system_prompt = None
    filtered_messages = []
    for msg in messages:
        if msg['role'] == 'system':
            system_prompt = msg['content']
        else:
            filtered_messages.append(msg)

    response = await async_anthropic_client.messages.create(
        model='claude-opus-4-20250514',
        max_tokens=1024,
        system=system_prompt if system_prompt else 'You are a helpful assistant.',
        messages=filtered_messages
    )

    return response.content[0].text


# ----------------------------------------------------------------------------
# Example 1.7: Multiple Prompts in One Trace
# ----------------------------------------------------------------------------

@trace()
async def example_multiple_prompts():
    """
    Using multiple prompts in one traced function.

    Each prompt can be linked independently. The last linked prompt's
    metadata will be associated with the span.
    """
    # First prompt: analyze
    analysis_prompt = await Prompt.aget(name='content-analyzer')
    analysis_compiled = analysis_prompt.compile({'content': 'Sample content to analyze'})
    analysis_messages = _ensure_messages(analysis_compiled)

    analysis = openai_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=analysis_messages
    )

    # Second prompt: summarize
    summary_prompt = await Prompt.aget(name='content-summarizer')
    summary_compiled = summary_prompt.compile({
        'content': analysis.choices[0].message.content
    })
    summary_messages = _ensure_messages(summary_compiled)

    summary = openai_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=summary_messages
    )

    return {
        'analysis': analysis.choices[0].message.content,
        'summary': summary.choices[0].message.content
    }


# ============================================================================
# SECTION 2: LANGCHAIN EXAMPLES
# ============================================================================

# ----------------------------------------------------------------------------
# Example 2.1: Basic LangChain Chain with Automatic Linking
# ----------------------------------------------------------------------------

async def example_langchain_basic():
    """
    Basic LangChain chain with automatic prompt linking.

    to_langchain() converts Beacon prompts to LangChain templates.
    BeaconCallbackHandler automatically captures metadata.
    """
    if not beacon_handler:
        print("LangChain not installed, skipping example")
        return

    # Fetch and convert to LangChain template
    prompt = await Prompt.aget(name='customer-greeting')
    lc_prompt = prompt.to_langchain()

    # Build chain
    # llm = ChatOpenAI(model='gpt-4o-mini')
    llm = chat_open_ai
    chain = lc_prompt | llm

    # Execute with BeaconCallbackHandler
    result = await chain.ainvoke(
        {'name': 'Ivy', 'company': 'ChainCo'},
        config={'callbacks': [beacon_handler]}
    )

    return result.content


# ----------------------------------------------------------------------------
# Example 2.2: LangChain with Output Parser
# ----------------------------------------------------------------------------

async def example_langchain_with_parser():
    """
    Full LangChain pipeline with output parser.

    Demonstrates integration of prompts with complete LCEL chains.
    """
    if not beacon_handler:
        print("LangChain not installed, skipping example")
        return

    prompt = await Prompt.aget(name='customer-greeting')
    lc_prompt = prompt.to_langchain()

    # llm = ChatOpenAI(model='gpt-4o-mini')
    llm = chat_open_ai
    parser = StrOutputParser()

    # Complete chain with parser
    chain = lc_prompt | llm | parser

    result = await chain.ainvoke(
        {'name': 'Jack', 'company': 'ParseTech'},
        config={'callbacks': [beacon_handler]}
    )

    return result


# ----------------------------------------------------------------------------
# Example 2.3: Multiple LangChain Chains
# ----------------------------------------------------------------------------

async def example_langchain_multiple_chains():
    """
    Using multiple different chains with different prompts.

    Each chain can use a different prompt, all captured in traces.
    """
    if not beacon_handler:
        print("LangChain not installed, skipping example")
        return

    # Chain 1: Analysis
    analysis_prompt = await Prompt.aget(name='content-analyzer')
    lc_analysis = analysis_prompt.to_langchain()

    # llm = ChatOpenAI(model='gpt-4o-mini')
    llm = chat_open_ai
    analysis_chain = lc_analysis | llm

    analysis_result = await analysis_chain.ainvoke(
        {'content': 'Some content to analyze'},
        config={'callbacks': [beacon_handler]}
    )

    # Chain 2: Summary
    summary_prompt = await Prompt.aget(name='content-summarizer')
    lc_summary = summary_prompt.to_langchain()

    summary_chain = lc_summary | llm

    summary_result = await summary_chain.ainvoke(
        {'content': analysis_result.content},
        config={'callbacks': [beacon_handler]}
    )

    return {
        'analysis': analysis_result.content,
        'summary': summary_result.content
    }


# ----------------------------------------------------------------------------
# Example 2.4: Synchronous LangChain Usage
# ----------------------------------------------------------------------------

def example_langchain_sync():
    """
    Synchronous LangChain usage with sync Beacon methods.

    Use .invoke() instead of .ainvoke() for sync execution.
    """
    if not beacon_handler:
        print("LangChain not installed, skipping example")
        return

    # Sync prompt fetch
    prompt = Prompt.get(name='customer-greeting')
    lc_prompt = prompt.to_langchain()

    # llm = ChatOpenAI(model='gpt-4o-mini')
    llm = chat_open_ai
    chain = lc_prompt | llm

    # Sync invocation
    result = chain.invoke(
        {'name': 'Kelly', 'company': 'SyncSystems'},
        config={'callbacks': [beacon_handler]}
    )

    return result.content


# ============================================================================
# SECTION 3: LANGGRAPH EXAMPLES
# ============================================================================

# ----------------------------------------------------------------------------
# Example 3.1: Basic LangGraph Single Node
# ----------------------------------------------------------------------------

async def example_langgraph_basic():
    """
    Basic LangGraph with single node using a prompt.

    LangGraph lets you build stateful, multi-step agent workflows.
    Prompts integrate seamlessly into graph nodes.
    """
    if not StateGraph or not beacon_handler:
        print("LangGraph not installed, skipping example")
        return

    # Define state
    class State(TypedDict):
        name: str
        company: str
        response: str

    # Node function using prompt
    async def greet_node(state: State):
        prompt = await Prompt.aget(name='customer-greeting')
        lc_prompt = prompt.to_langchain()

        llm = chat_open_ai
        chain = lc_prompt | llm

        result = await chain.ainvoke(
            {'name': state['name'], 'company': state['company']},
            config={'callbacks': [beacon_handler]}
        )

        return {'response': result.content}

    # Build graph
    graph = StateGraph(State)
    graph.add_node('greet', greet_node)
    graph.set_entry_point('greet')
    graph.set_finish_point('greet')

    app = graph.compile()

    # Run graph
    result = await app.ainvoke({
        'name': 'Laura',
        'company': 'GraphTech'
    })

    return result['response']


# ----------------------------------------------------------------------------
# Example 3.2: Multi-Step LangGraph Workflow
# ----------------------------------------------------------------------------

async def example_langgraph_multi_step():
    """
    Multi-step LangGraph workflow: analysis -> summary.

    Different nodes use different prompts, creating a pipeline.
    """
    if not StateGraph or not beacon_handler:
        print("LangGraph not installed, skipping example")
        return

    class State(TypedDict):
        content: str
        analysis: str
        summary: str

    async def analyze_node(state: State):
        prompt = await Prompt.aget(name='content-analyzer')
        lc_prompt = prompt.to_langchain()

        llm = chat_open_ai
        chain = lc_prompt | llm

        result = await chain.ainvoke(
            {'content': state['content']},
            config={'callbacks': [beacon_handler]}
        )

        return {'analysis': result.content}

    async def summarize_node(state: State):
        prompt = await Prompt.aget(name='content-summarizer')
        lc_prompt = prompt.to_langchain()

        llm = chat_open_ai
        chain = lc_prompt | llm

        result = await chain.ainvoke(
            {'content': state['analysis']},
            config={'callbacks': [beacon_handler]}
        )

        return {'summary': result.content}

    # Build graph
    graph = StateGraph(State)
    graph.add_node('analyze', analyze_node)
    graph.add_node('summarize', summarize_node)
    graph.add_edge('analyze', 'summarize')
    graph.set_entry_point('analyze')
    graph.set_finish_point('summarize')

    app = graph.compile()

    result = await app.ainvoke({
        'content': 'Article content to process...'
    })

    return result


# ----------------------------------------------------------------------------
# Example 3.3: Conditional Routing with Different Prompts
# ----------------------------------------------------------------------------

async def example_langgraph_conditional():
    """
    Conditional routing in LangGraph using different prompts per path.

    Routes to different nodes (support vs sales) based on input,
    each using appropriate prompts.
    """
    if not StateGraph or not beacon_handler:
        print("LangGraph not installed, skipping example")
        return

    class State(TypedDict):
        query_type: str  # 'support' or 'sales'
        customer_name: str
        response: str

    async def support_node(state: State):
        prompt = await Prompt.aget(name='support-response')
        lc_prompt = prompt.to_langchain()

        llm = chat_open_ai
        chain = lc_prompt | llm

        result = await chain.ainvoke(
            {'customer_name': state['customer_name']},
            config={'callbacks': [beacon_handler]}
        )

        return {'response': result.content}

    async def sales_node(state: State):
        prompt = await Prompt.aget(name='sales-response')
        lc_prompt = prompt.to_langchain()

        llm = chat_open_ai
        chain = lc_prompt | llm

        result = await chain.ainvoke(
            {'customer_name': state['customer_name']},
            config={'callbacks': [beacon_handler]}
        )

        return {'response': result.content}

    def route(state: State):
        if state['query_type'] == 'support':
            return 'support'
        else:
            return 'sales'

    # Build graph
    graph = StateGraph(State)
    graph.add_node('support', support_node)
    graph.add_node('sales', sales_node)
    graph.add_conditional_edges(
        '__start__',
        route,
        {'support': 'support', 'sales': 'sales'}
    )
    graph.set_finish_point('support')
    graph.set_finish_point('sales')

    app = graph.compile()

    result = await app.ainvoke({
        'query_type': 'support',
        'customer_name': 'Michael'
    })

    return result['response']


# ----------------------------------------------------------------------------
# Example 3.4: LangGraph Agent with Tools
# ----------------------------------------------------------------------------

async def example_langgraph_with_tools():
    """
    LangGraph agent with tools and prompts.

    Combines tool calling with prompt-based responses for complex agents.
    """
    if not StateGraph or not beacon_handler:
        print("LangGraph not installed, skipping example")
        return

    from langchain_core.tools import tool

    @tool
    def get_customer_info(customer_id: str) -> dict:
        """Retrieve customer information from database."""
        return {
            'name': 'Nancy',
            'company': 'ToolCorp',
            'tier': 'premium'
        }

    class State(TypedDict):
        customer_id: str
        customer_info: dict
        response: str

    async def fetch_info_node(state: State):
        customer_info = get_customer_info(state['customer_id'])
        return {'customer_info': customer_info}

    async def generate_response_node(state: State):
        prompt = await Prompt.aget(name='customer-greeting')
        lc_prompt = prompt.to_langchain()

        llm = chat_open_ai
        chain = lc_prompt | llm

        result = await chain.ainvoke(
            {
                'name': state['customer_info']['name'],
                'company': state['customer_info']['company']
            },
            config={'callbacks': [beacon_handler]}
        )

        return {'response': result.content}

    # Build graph
    graph = StateGraph(State)
    graph.add_node('fetch_info', fetch_info_node)
    graph.add_node('generate_response', generate_response_node)
    graph.add_edge('fetch_info', 'generate_response')
    graph.set_entry_point('fetch_info')
    graph.set_finish_point('generate_response')

    app = graph.compile()

    result = await app.ainvoke({
        'customer_id': 'cust_123'
    })

    return result['response']


# ============================================================================
# SECTION 4: BEST PRACTICES & REFERENCE
# ============================================================================

def print_best_practices():
    """
    Quick reference guide for prompt linking best practices.
    """
    guide = """
    ============================================================================
    PROMPT LINKING BEST PRACTICES
    ============================================================================

    1. CHOOSING THE RIGHT METHOD:
       - OpenAI/Anthropic: Use compile() with @trace() for automatic linking
       - LangChain: Use to_langchain() with BeaconCallbackHandler
       - LangGraph: Same as LangChain, works seamlessly in nodes
       - Manual control: Use link_to_span() for custom scenarios

    2. LABEL MANAGEMENT:
       - Use 'production' label for production prompts
       - Use 'staging' for testing
       - Use 'latest' (default) for most recent version
       - Label-based fetching: Prompt.get('name', label='production')

    3. METADATA CAPTURED IN TRACES:
       - prompt.id: Unique prompt identifier
       - prompt.name: Human-readable prompt name
       - prompt.version: Version number
       - prompt.labels: List of labels (e.g., ['production', 'v2'])
       - prompt.tags: Custom tags for organization

    4. ASYNC VS SYNC:
       - Prefer async methods (aget, acreate, aupdate) for better performance
       - Use sync methods (get, create, update) only when necessary
       - Never mix async/sync in the same function

    5. ERROR HANDLING:
       - PromptNotFoundError: Prompt doesn't exist
       - PromptValidationError: Invalid parameters
       - PromptNetworkError: Connection issues
       - Always handle exceptions in production code

    6. PRODUCTION CHECKLIST:
       - Set up proper error handling
       - Use labels to manage versions across environments
       - Monitor prompt usage in Beacon dashboard
       - Test prompts before deploying to production
       - Keep prompt templates in version control
       - Document expected variables for each prompt

    7. DISABLING AUTO-LINK:
       - Use auto_link=False when testing
       - Use when you want manual control over linking
       - Useful for conditional linking logic

    8. MULTIPLE PROMPTS:
       - Each compile() or to_langchain() can link independently
       - Last linked prompt wins for span metadata
       - Consider using nested spans for complex workflows

    ============================================================================
    """
    print(guide)


# ============================================================================
# MAIN CLI
# ============================================================================

async def main():
    """
    Main function demonstrating various prompt linking examples.

    Uncomment specific examples to run them.
    """
    print("=" * 80)
    print("LUMENOVA BEACON - COMPLETE PROMPT LINKING GUIDE")
    print("=" * 80)
    print()

    # Print best practices
    print_best_practices()
    print()

    # ========================================================================
    # SECTION 1: Direct LLM SDK Examples
    # ========================================================================

    print("SECTION 1: DIRECT LLM SDK EXAMPLES")
    print("-" * 80)

    if openai_client:
        print("\n[Example 1.1] Basic OpenAI Linking:")
        # result = await example_basic_openai_linking()
        # print(result)

        print("\n[Example 1.2] Version-Specific Prompt:")
        # result = await example_version_specific_prompt()
        # print(result)

        print("\n[Example 1.3] Manual Linking:")
        # result = await example_manual_linking()
        # print(result)

        print("\n[Example 1.4] Disable Auto-Linking:")
        # result = await example_disable_auto_linking()
        # print(result)

        # print("\n[Example 1.5] Sync Usage:")
        # result = example_sync_prompt_usage()
        # print(result)

        print("\n[Example 1.7] Multiple Prompts:")
        # result = await example_multiple_prompts()
        # print(result)

    if anthropic_client:
        print("\n[Example 1.6a] Anthropic System Prompt:")
        # result = await example_anthropic_system_prompt()
        # print(result)

        print("\n[Example 1.6b] Anthropic Streaming:")
        # result = await example_anthropic_streaming()
        # print(result)

        print("\n[Example 1.6c] Anthropic Async:")
        # result = await example_anthropic_async()
        # print(result)

    # ========================================================================
    # SECTION 2: LangChain Examples
    # ========================================================================

    print("\n\nSECTION 2: LANGCHAIN EXAMPLES")
    print("-" * 80)

    if beacon_handler:
        print("\n[Example 2.1] Basic LangChain:")
        # result = await example_langchain_basic()
        # print(result)

        print("\n[Example 2.2] LangChain with Parser:")
        # result = await example_langchain_with_parser()
        # print(result)

        print("\n[Example 2.3] Multiple Chains:")
        # result = await example_langchain_multiple_chains()
        # print(result)

        # print("\n[Example 2.4] Sync LangChain:")
        # result = example_langchain_sync()
        # print(result)

    # ========================================================================
    # SECTION 3: LangGraph Examples
    # ========================================================================

    print("\n\nSECTION 3: LANGGRAPH EXAMPLES")
    print("-" * 80)

    if StateGraph and beacon_handler:
        print("\n[Example 3.1] Basic LangGraph:")
        # result = await example_langgraph_basic()
        # print(result)

        print("\n[Example 3.2] Multi-Step Workflow:")
        # result = await example_langgraph_multi_step()
        # print(result)

        print("\n[Example 3.3] Conditional Routing:")
        # result = await example_langgraph_conditional()
        # print(result)

        print("\n[Example 3.4] Agent with Tools:")
        # result = await example_langgraph_with_tools()
        # print(result)

    print("\n" + "=" * 80)
    print("Examples complete! Uncomment specific examples in main() to run them.")
    print("=" * 80)


if __name__ == '__main__':
    asyncio.run(main())
