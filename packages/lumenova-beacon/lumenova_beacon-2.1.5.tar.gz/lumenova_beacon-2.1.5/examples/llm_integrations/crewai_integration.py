"""CrewAI Integration with Beacon via OpenTelemetry - With Tool Tracing.

CrewAI is a multi-agent framework that uses LiteLLM internally for LLM operations.
This requires TWO instrumentors for complete observability:

1. CrewAIInstrumentor - Captures high-level agent/task/crew orchestration AND tool calls
2. LiteLLMInstrumentor - Captures low-level LLM API calls (token usage, prompts, etc.)

Why both? CrewAI uses LiteLLM as a universal proxy to connect to any LLM provider.
Without both instrumentors, you'd either see agent structure without LLM details,
or raw LLM calls without agent context.

Requirements:
    pip install lumenova-beacon[opentelemetry,crewai] python-dotenv
"""

import os
import dotenv
from lumenova_beacon import BeaconClient
from openinference.instrumentation.crewai import CrewAIInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

dotenv.load_dotenv()

# === Step 1: Initialize Beacon FIRST ===
# Note: auto_instrument_litellm defaults to False to avoid duplicate spans
# when using LiteLLMInstrumentor explicitly
beacon_client = BeaconClient()

# === Step 2: Instrument CrewAI and LiteLLM ===
# Both instrumentors are required for complete observability:
# - CrewAIInstrumentor: Captures agent orchestration, task execution, crew workflows, AND tool calls
# - LiteLLMInstrumentor: Captures LLM API calls, token usage, prompts/completions
CrewAIInstrumentor().instrument(skip_dep_check=True)
LiteLLMInstrumentor().instrument()

# === Step 3: Define Custom Tools ===
@tool("Calculator Tool")
def calculator(expression: str) -> str:
    """Evaluates mathematical expressions safely.
    Input should be a valid Python expression like '2 + 2' or '10 * (5 + 3)'.
    Useful for performing calculations during analysis."""
    try:
        # Use a safer eval approach by restricting builtins
        result = eval(expression, {"__builtins__": {}}, {})
        return f"The result of '{expression}' is {result}"
    except Exception as e:
        return f"Error: Unable to calculate '{expression}'. {str(e)}"


@tool("Search Simulator Tool")
def search_simulator(query: str) -> str:
    """Simulates a search for information (returns mock data for demonstration).
    Input should be a search query string.
    Useful for gathering information during research."""
    # Mock search results for demonstration purposes
    mock_data = {
        "ai": "Recent AI advancements include GPT-4, Claude 3 Opus/Sonnet, Gemini 1.5 Pro, and improved multimodal models in 2024. Key trends: agentic AI, improved reasoning, and enterprise adoption.",
        "data science": "Key 2024 trends: AutoML platforms, MLOps automation, edge computing analytics, and real-time decision systems. Focus on democratizing ML and production readiness.",
        "machine learning": "Focus areas: Few-shot learning, federated learning, ethical AI frameworks, and model interpretability. Emphasis on responsible AI development.",
        "llm": "Large Language Models in 2024: Extended context windows (100K+ tokens), improved factuality, reduced hallucinations, and better tool use capabilities.",
    }

    query_lower = query.lower()
    for key, value in mock_data.items():
        if key in query_lower:
            return f"Search results for '{query}': {value}"

    return f"Search results for '{query}': General information available. Consider refining your query with terms like 'AI', 'data science', 'machine learning', or 'LLM'."


@tool("Word Counter Tool")
def word_counter(text: str) -> str:
    """Counts words, characters, and sentences in a text.
    Input should be any text string.
    Useful for analyzing content length and structure."""
    words = len(text.split())
    chars = len(text)
    sentences = text.count('.') + text.count('!') + text.count('?')

    return f"Text Analysis: {words} words, {chars} characters, {sentences} sentences"


@tool("Text Analyzer Tool")
def text_analyzer(text: str) -> str:
    """Analyzes text readability and complexity metrics.
    Input should be a paragraph or longer text.
    Useful for evaluating content quality and readability."""
    words = text.split()
    word_count = len(words)

    if word_count == 0:
        return "Error: Text is empty"

    avg_word_length = sum(len(word) for word in words) / word_count

    # Count complex words (>8 characters)
    complex_words = sum(1 for word in words if len(word) > 8)
    complexity_ratio = (complex_words / word_count) * 100

    readability = "Easy" if complexity_ratio < 10 else "Medium" if complexity_ratio < 20 else "Complex"

    return (f"Readability: {readability} | "
            f"Avg word length: {avg_word_length:.1f} chars | "
            f"Complex words: {complex_words}/{word_count} ({complexity_ratio:.1f}%)")


# === Step 4: Configure Azure OpenAI via LiteLLM ===
AZURE_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
AZURE_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

if not AZURE_API_KEY or not AZURE_ENDPOINT:
    print("Error: AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set")
    exit(1)

# Set environment variables as LiteLLM expects
os.environ['AZURE_API_KEY'] = AZURE_API_KEY
os.environ['AZURE_API_BASE'] = AZURE_ENDPOINT
os.environ['AZURE_API_VERSION'] = AZURE_API_VERSION

# Create LLM instance using Azure OpenAI
llm = LLM(model=f'azure/{AZURE_DEPLOYMENT}')

# === Step 5: Define CrewAI Agents with Tools ===
researcher = Agent(
    role='Senior Research Analyst',
    goal='Uncover cutting-edge developments in AI and data science',
    backstory="""You work at a leading tech think tank.
    Your expertise lies in identifying emerging trends.
    You have a knack for dissecting complex data and presenting actionable insights.""",
    verbose=True,
    allow_delegation=False,
    tools=[calculator, search_simulator],  # Analytical tools for research
    llm=llm
)

writer = Agent(
    role='Tech Content Strategist',
    goal='Craft compelling content on tech advancements',
    backstory="""You are a renowned Content Strategist, known for your insightful
    and engaging articles. You transform complex concepts into compelling narratives.
    You always check your content quality using available tools.""",
    verbose=True,
    allow_delegation=True,
    tools=[word_counter, text_analyzer],  # Content quality tools for writing
    llm=llm
)

# === Step 6: Define Tasks ===
task1 = Task(
    description="""Conduct a comprehensive analysis of the latest advancements in AI in 2024.
    Use the search simulator tool to gather information about recent AI developments.
    If you need to perform any calculations or data analysis, use the calculator tool.
    Identify key trends, breakthrough technologies, and potential industry impacts.
    Focus on practical applications and real-world impact.""",
    expected_output="Full analysis report in bullet points with at least 5 key findings",
    agent=researcher
)

task2 = Task(
    description="""Using the insights provided, develop an engaging blog post
    that highlights the most significant AI advancements.
    Your post should be informative yet accessible, catering to a tech-savvy audience.
    Make it sound cool and engaging, avoid overly complex jargon.
    After writing the post, use the word counter tool to check the length
    and the text analyzer tool to verify readability.""",
    expected_output="Full blog post of at least 4 paragraphs with an engaging title, followed by quality metrics",
    agent=writer
)

# === Step 7: Create Crew ===
# The Crew orchestrates how agents work together on tasks
crew = Crew(
    agents=[researcher, writer],
    tasks=[task1, task2],
    verbose=True,
    process=Process.sequential  # Tasks executed in order
)

# === Step 8: Execute Crew - All Spans Automatically Traced to Beacon ===
try:
    result = crew.kickoff()
    print("CREW EXECUTION COMPLETED")
    print(result)
except Exception as e:
    print(f"\nError during crew execution: {e}")
