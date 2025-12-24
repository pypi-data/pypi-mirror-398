"""This example demonstrates building a RAG pipeline with LangChain and tracing all operations
using BeaconCallbackHandler. The pipeline combines document retrieval with LLM generation.

Requirements:
    pip install lumenova-beacon[langchain]
    pip install langchain-openai langchain-community faiss-cpu tiktoken
"""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from lumenova_beacon import BeaconCallbackHandler

import dotenv

dotenv.load_dotenv()

# Create the callback handler for tracing
handler = BeaconCallbackHandler()

# === Step 1: Create Sample Documents ===
# Build a knowledge base about Python programming
documents = [
    Document(
        page_content="Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991.",
        metadata={"source": "python_intro.txt", "topic": "basics"}
    ),
    Document(
        page_content="Python supports multiple programming paradigms including procedural, object-oriented, and functional programming. It has a comprehensive standard library.",
        metadata={"source": "python_features.txt", "topic": "features"}
    ),
    Document(
        page_content="List comprehensions in Python provide a concise way to create lists. For example: squares = [x**2 for x in range(10)] creates a list of squares.",
        metadata={"source": "python_comprehensions.txt", "topic": "syntax"}
    ),
    Document(
        page_content="Python decorators are a powerful feature that allows you to modify the behavior of functions or classes. They are defined using the @decorator_name syntax.",
        metadata={"source": "python_decorators.txt", "topic": "advanced"}
    ),
    Document(
        page_content="Python's async/await syntax enables asynchronous programming. It allows you to write concurrent code that can handle I/O-bound operations efficiently.",
        metadata={"source": "python_async.txt", "topic": "advanced"}
    ),
    Document(
        page_content="Virtual environments in Python (venv) allow you to create isolated Python environments with their own dependencies, preventing package conflicts.",
        metadata={"source": "python_venv.txt", "topic": "tools"}
    ),
]
print(f"Created {len(documents)} documents")


# === Step 2: Create Embeddings and Vector Store ===
# Use OpenAI embeddings and FAISS for semantic search
try:
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
except Exception as e:
    print(f"⚠ Error creating vector store: {e}")
    print("  Make sure OPENAI_API_KEY is set")
    exit(1)


# === Step 3: Create Retriever ===
# Configure to return top 3 most relevant documents
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)


# === Step 4: Create RAG Prompt Template ===
template = """You are a helpful assistant answering questions about Python programming.
Use the following context to answer the question. If you cannot answer based on the context, say so.

Context:
{context}

Question: {question}

Answer:"""

prompt = ChatPromptTemplate.from_template(template)

# === Step 5: Initialize LLM ===
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# === Step 6: Build RAG Chain ===
# Assemble the chain using LCEL (LangChain Expression Language)


def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)


# Chain structure:
# 1. Retriever finds relevant documents
# 2. Context formatter combines retrieved docs
# 3. Prompt inserts context and question
# 4. LLM generates answer
# 5. Parser extracts text response
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)


# === Step 7: Run RAG Queries with Tracing ===
questions = [
    "How do list comprehensions work in Python?",
    # "What is Python and who created it?",
    # "What are Python decorators?",
]

for i, question in enumerate(questions, 1):
    print(f"\nQuery {i}: {question}")

    try:
        # Invoke the RAG chain with BeaconCallbackHandler
        # This traces: retrieval, chain execution, and LLM generation
        answer = rag_chain.invoke(
            question,
            config={"callbacks": [handler]}
        )

        print(f"Answer: {answer}")

    except Exception as e:
        print(f"⚠ Error: {e}")

# Check your Beacon dashboard to see:
# - Retrieval spans (vector store queries with retrieved documents)
# - Chain span (overall RAG chain execution)
# - Generation span (LLM answering with context)
# - Complete trace hierarchy showing RAG pipeline
