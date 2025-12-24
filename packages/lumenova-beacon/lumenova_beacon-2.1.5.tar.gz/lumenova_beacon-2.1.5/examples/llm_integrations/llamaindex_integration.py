"""This example demonstrates automatic LlamaIndex RAG tracing using OpenTelemetry and Beacon SDK.

Requirements:
    pip install lumenova-beacon[opentelemetry,examples]
    pip install llama-index-llms-azure-openai llama-index-embeddings-azure-openai
"""

import os
import dotenv
from opentelemetry import trace
from lumenova_beacon import BeaconClient

dotenv.load_dotenv()

# === Step 1: Initialize Beacon FIRST ===
beacon_client = BeaconClient()

# === Step 2: Instrument LlamaIndex ===
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

LlamaIndexInstrumentor().instrument()

# === Step 3: Configure Azure OpenAI ===
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

Settings.llm = AzureOpenAI(
    model="gpt-4o-mini",
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

Settings.embed_model = AzureOpenAIEmbedding(
    model="text-embedding-3-large",
    deployment_name=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# === Example 1: Basic RAG Query ===
documents = [
    Document(
        text="Artificial Intelligence (AI) is the simulation of human intelligence by machines. "
             "It includes machine learning, natural language processing, and computer vision.",
        metadata={"source": "ai_basics.txt", "topic": "AI"}
    ),
    Document(
        text="Machine Learning is a subset of AI that focuses on algorithms learning from data. "
             "Types include supervised, unsupervised, and reinforcement learning.",
        metadata={"source": "ml_basics.txt", "topic": "ML"}
    ),
    Document(
        text="Large Language Models (LLMs) are AI models trained on vast text data. "
             "Examples include GPT-4, Claude, and PaLM. They can understand and generate human-like text.",
        metadata={"source": "llm_basics.txt", "topic": "LLMs"}
    ),
]

index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(similarity_top_k=2)

response = query_engine.query("What is artificial intelligence?")
print(f"Response: {response.response}")
print(f"Sources: {len(response.source_nodes)} documents retrieved\n")


# === Example 2: Multi-Query Conversation ===
queries = [
    "What is machine learning?",
    "What are the types of machine learning?",
    "Give me examples of LLMs"
]

for query_text in queries:
    response = query_engine.query(query_text)
    print(f"Q: {query_text}")
    print(f"A: {response.response[:100]}...\n")


# === Example 3: Custom Parent Spans for Grouping ===
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("research_session") as parent_span:
    parent_span.set_attribute("session.id", "research-123")
    parent_span.set_attribute("user.id", "researcher@example.com")

    response1 = query_engine.query("Explain AI in simple terms")
    response2 = query_engine.query("How does machine learning work?")

    parent_span.set_attribute("queries_count", 2)
    print(f"Research query 1: {response1.response[:80]}...")
    print(f"Research query 2: {response2.response[:80]}...\n")


# === Example 4: RAG with Rich Metadata ===
tech_docs = [
    Document(
        text="Python is a high-level programming language known for simplicity and readability. "
             "It's widely used for web development, data science, and machine learning.",
        metadata={"language": "Python", "difficulty": "beginner", "category": "programming"}
    ),
    Document(
        text="FastAPI is a modern web framework for building APIs with Python. "
             "It uses type hints and provides automatic API documentation.",
        metadata={"language": "Python", "difficulty": "intermediate", "category": "web"}
    ),
]

tech_index = VectorStoreIndex.from_documents(tech_docs)
tech_engine = tech_index.as_query_engine()

with tracer.start_as_current_span(
    "technical_query",
    attributes={
        "query.category": "programming",
        "query.language": "en",
        "user.role": "developer",
    }
) as span:
    response = tech_engine.query("What is Python used for?")
    span.set_attribute("response.length", len(response.response))
    print(f"Tech query: {response.response}\n")


# === Example 5: Query with Custom Retrieval Parameters ===
custom_engine = index.as_query_engine(
    similarity_top_k=3,  # Retrieve top 3 documents
    response_mode="compact",  # Compact response mode
)

response = custom_engine.query("Tell me about LLMs")
print(f"Custom retrieval: {response.response}")
print(f"Retrieved {len(response.source_nodes)} chunks\n")


# === Example 6: Session-Based Multi-Turn Interaction ===
with tracer.start_as_current_span(
    "user_session",
    attributes={
        "session.id": "session-abc123",
        "user.id": "alice@company.com",
    }
):
    print("=== User Session ===")

    # Turn 1
    with tracer.start_as_current_span("turn_1", attributes={"turn.number": 1}):
        response = query_engine.query("What is AI?")
        print(f"Turn 1: {response.response[:80]}...")

    # Turn 2
    with tracer.start_as_current_span("turn_2", attributes={"turn.number": 2}):
        response = query_engine.query("How is it different from ML?")
        print(f"Turn 2: {response.response[:80]}...")

    # Turn 3
    with tracer.start_as_current_span("turn_3", attributes={"turn.number": 3}):
        response = query_engine.query("Give me practical applications")
        print(f"Turn 3: {response.response[:80]}...\n")


# === Example 7: Query with Filters (Metadata-Based Retrieval) ===
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

filtered_engine = tech_index.as_query_engine(
    filters=MetadataFilters(
        filters=[ExactMatchFilter(key="category", value="programming")]
    ),
    similarity_top_k=1
)

response = filtered_engine.query("Tell me about programming languages")
print(f"Filtered query: {response.response}\n")


# === Example 8: Building Index from Multiple Sources ===
knowledge_base = [
    Document(text="OpenTelemetry is an observability framework.", metadata={"source": "otel_docs"}),
    Document(text="Beacon SDK provides observability for LLM applications.", metadata={"source": "beacon_docs"}),
    Document(text="LlamaIndex is a data framework for LLM apps.", metadata={"source": "llama_docs"}),
]

kb_index = VectorStoreIndex.from_documents(knowledge_base)
kb_engine = kb_index.as_query_engine()

with tracer.start_as_current_span("knowledge_base_query"):
    response = kb_engine.query("What tools are available for LLM observability?")
    print(f"Knowledge base: {response.response}\n")
