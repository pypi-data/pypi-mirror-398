"""Tests for LangChain integration."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from lumenova_beacon import BeaconClient, BeaconCallbackHandler
from lumenova_beacon.types import SpanType, SpanKind, StatusCode


@pytest.fixture
def mock_client():
    """Create a mock BeaconClient."""
    client = MagicMock(spec=BeaconClient)
    client.should_sample = MagicMock(return_value=True)
    return client


@pytest.fixture
def handler(mock_client):
    """Create a BeaconCallbackHandler with mock client."""
    with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
        mock_get.return_value = mock_client
        return BeaconCallbackHandler()


class TestBeaconCallbackHandler:
    """Test suite for BeaconCallbackHandler."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            mock_client = MagicMock(spec=BeaconClient)
            mock_get.return_value = mock_client
            handler = BeaconCallbackHandler()
            assert handler.client == mock_client
            assert handler._runs == {}
            assert handler._session_id is None

    def test_init_with_custom_parameters(self):
        """Test initialization with custom session_id."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            mock_client = MagicMock(spec=BeaconClient)
            mock_get.return_value = mock_client
            handler = BeaconCallbackHandler(
                session_id="test-session"
            )
            assert handler.client is not None
            assert handler._session_id == "test-session"
            mock_get.assert_called_once()

    def test_on_chain_start(self, handler, mock_client):
        """Test chain start event creates span."""
        run_id = uuid4()
        serialized = {"name": "TestChain", "id": ["test", "chain"]}
        inputs = {"query": "test question"}
        metadata = {"user_id": "123"}
        tags = ["test", "chain"]

        handler.on_chain_start(
            serialized=serialized,
            inputs=inputs,
            run_id=run_id,
            metadata=metadata,
            tags=tags,
        )

        # Check run was created
        run_id_str = str(run_id)
        assert run_id_str in handler._runs
        run_data = handler._runs[run_id_str]

        # Check span properties
        span = run_data["span"]
        assert span.name == "TestChain"
        assert span.span_type == SpanType.CHAIN
        assert span.kind == SpanKind.INTERNAL
        assert span.start_time is not None

        # Check attributes
        assert "langchain.input" in span.attributes
        assert "langchain.metadata.user_id" in span.attributes
        assert "langchain.metadata.tags" in span.attributes

    def test_on_chain_end(self, handler, mock_client):
        """Test chain end event finalizes and sends span."""
        run_id = uuid4()

        # Start chain first
        handler.on_chain_start(
            serialized={"name": "TestChain"},
            inputs={"query": "test"},
            run_id=run_id,
        )

        # End chain
        outputs = {"result": "test answer"}
        handler.on_chain_end(outputs=outputs, run_id=run_id)

        # Check span was sent
        mock_client.export_span.assert_called_once()
        sent_span = mock_client.export_span.call_args[0][0]

        # Check span properties
        assert sent_span.end_time is not None
        assert sent_span.status_code == StatusCode.OK
        assert "langchain.output" in sent_span.attributes

        # Check run was cleaned up
        assert str(run_id) not in handler._runs

    def test_on_chain_error(self, handler, mock_client):
        """Test chain error event records exception."""
        run_id = uuid4()

        # Start chain first
        handler.on_chain_start(
            serialized={"name": "TestChain"},
            inputs={"query": "test"},
            run_id=run_id,
        )

        # Error
        error = ValueError("Test error")
        handler.on_chain_error(error=error, run_id=run_id)

        # Check span was sent with error
        mock_client.export_span.assert_called_once()
        sent_span = mock_client.export_span.call_args[0][0]

        # Check error was recorded
        assert sent_span.status_code == StatusCode.ERROR
        assert sent_span.status_description == "Test error"
        assert "exception.type" in sent_span.attributes
        assert "exception.message" in sent_span.attributes

    def test_on_llm_start(self, handler, mock_client):
        """Test LLM start event creates generation span."""
        run_id = uuid4()
        serialized = {
            "name": "ChatOpenAI",
            "kwargs": {"model_name": "gpt-4"},
        }
        prompts = ["What is the capital of France?"]

        handler.on_llm_start(
            serialized=serialized,
            prompts=prompts,
            run_id=run_id,
        )

        # Check run was created
        run_id_str = str(run_id)
        assert run_id_str in handler._runs
        span = handler._runs[run_id_str]["span"]

        # Check span properties
        assert span.span_type == SpanType.GENERATION
        assert span.kind == SpanKind.CLIENT
        assert "langchain.input" in span.attributes
        assert "gen_ai.request.model" in span.attributes
        assert span.attributes["gen_ai.request.model"] == "gpt-4"

    def test_on_chat_model_start(self, handler, mock_client):
        """Test chat model start event."""
        from unittest.mock import MagicMock

        run_id = uuid4()
        serialized = {"name": "ChatOpenAI"}

        # Mock message objects
        message1 = MagicMock()
        message1.type = "human"
        message1.content = "Hello"

        messages = [[message1]]

        handler.on_chat_model_start(
            serialized=serialized,
            messages=messages,
            run_id=run_id,
        )

        # Check span was created
        assert str(run_id) in handler._runs
        span = handler._runs[str(run_id)]["span"]
        assert span.span_type == SpanType.GENERATION

    def test_on_llm_end_with_token_usage(self, handler, mock_client):
        """Test LLM end event extracts token usage."""
        from unittest.mock import MagicMock

        run_id = uuid4()

        # Start LLM first
        handler.on_llm_start(
            serialized={"name": "ChatOpenAI"},
            prompts=["test"],
            run_id=run_id,
        )

        # Mock LLMResult with token usage
        response = MagicMock()
        generation = MagicMock()
        generation.text = "Paris"
        generation.message = None
        response.generations = [[generation]]
        response.llm_output = {
            "token_usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
            "model_name": "gpt-4",
        }

        handler.on_llm_end(response=response, run_id=run_id)

        # Check token usage was captured as individual attributes
        sent_span = mock_client.export_span.call_args[0][0]
        assert "gen_ai.usage.prompt_tokens" in sent_span.attributes
        assert "gen_ai.usage.completion_tokens" in sent_span.attributes
        assert "gen_ai.usage.total_tokens" in sent_span.attributes

        # Verify token counts
        assert sent_span.attributes["gen_ai.usage.prompt_tokens"] == 10
        assert sent_span.attributes["gen_ai.usage.completion_tokens"] == 5
        assert sent_span.attributes["gen_ai.usage.total_tokens"] == 15

        # Verify model name was captured
        assert "gen_ai.request.model" in sent_span.attributes
        assert sent_span.attributes["gen_ai.request.model"] == "gpt-4"

    def test_on_tool_start(self, handler, mock_client):
        """Test tool start event."""
        run_id = uuid4()
        serialized = {"name": "Calculator"}
        input_str = "2 + 2"

        handler.on_tool_start(
            serialized=serialized,
            input_str=input_str,
            run_id=run_id,
        )

        # Check span was created
        assert str(run_id) in handler._runs
        span = handler._runs[str(run_id)]["span"]
        assert span.span_type == SpanType.TOOL
        assert span.kind == SpanKind.INTERNAL

    def test_on_tool_end(self, handler, mock_client):
        """Test tool end event."""
        run_id = uuid4()

        # Start tool first
        handler.on_tool_start(
            serialized={"name": "Calculator"},
            input_str="2 + 2",
            run_id=run_id,
        )

        # End tool
        output = "4"
        handler.on_tool_end(output=output, run_id=run_id)

        # Check span was sent
        mock_client.export_span.assert_called_once()
        sent_span = mock_client.export_span.call_args[0][0]
        assert "langchain.output" in sent_span.attributes

    def test_on_retriever_start(self, handler, mock_client):
        """Test retriever start event."""
        run_id = uuid4()
        serialized = {"name": "VectorStoreRetriever"}
        query = "test query"

        handler.on_retriever_start(
            serialized=serialized,
            query=query,
            run_id=run_id,
        )

        # Check span was created
        assert str(run_id) in handler._runs
        span = handler._runs[str(run_id)]["span"]
        assert span.span_type == SpanType.RETRIEVAL

    def test_on_retriever_end(self, handler, mock_client):
        """Test retriever end event."""
        from unittest.mock import MagicMock

        run_id = uuid4()

        # Start retriever first
        handler.on_retriever_start(
            serialized={"name": "VectorStoreRetriever"},
            query="test",
            run_id=run_id,
        )

        # Mock documents
        doc1 = MagicMock()
        doc1.page_content = "Document 1"
        doc1.metadata = {"source": "test.txt"}

        documents = [doc1]

        handler.on_retriever_end(documents=documents, run_id=run_id)

        # Check span was sent
        sent_span = mock_client.export_span.call_args[0][0]
        assert "langchain.output" in sent_span.attributes
        assert "retriever.document_count" in sent_span.attributes

    def test_parent_child_relationship(self, handler, mock_client):
        """Test parent-child span relationships."""
        parent_run_id = uuid4()
        child_run_id = uuid4()

        # Start parent chain
        handler.on_chain_start(
            serialized={"name": "ParentChain"},
            inputs={"query": "test"},
            run_id=parent_run_id,
        )

        # Start child LLM
        handler.on_llm_start(
            serialized={"name": "ChildLLM"},
            prompts=["test"],
            run_id=child_run_id,
            parent_run_id=parent_run_id,
        )

        # Check parent-child relationship
        parent_span = handler._runs[str(parent_run_id)]["span"]
        child_span = handler._runs[str(child_run_id)]["span"]

        assert child_span.parent_id == parent_span.span_id
        assert child_span.trace_id == parent_span.trace_id

    def test_on_agent_action(self, handler, mock_client):
        """Test agent action event."""
        from unittest.mock import MagicMock

        parent_run_id = uuid4()
        action_run_id = uuid4()

        # Start parent agent chain
        handler.on_chain_start(
            serialized={"name": "AgentExecutor"},
            inputs={"input": "test"},
            run_id=parent_run_id,
        )

        # Record agent action
        action = MagicMock()
        action.tool = "Calculator"
        action.tool_input = "2 + 2"
        action.log = "Thought: I need to calculate 2 + 2"

        handler.on_agent_action(
            action=action,
            run_id=action_run_id,
            parent_run_id=parent_run_id,
        )

        # Check action was recorded in parent span
        parent_span = handler._runs[str(parent_run_id)]["span"]
        action_key = f"agent.action.{str(action_run_id)[:8]}"
        assert action_key in parent_span.attributes

    def test_on_agent_finish(self, handler, mock_client):
        """Test agent finish event."""
        from unittest.mock import MagicMock

        parent_run_id = uuid4()
        finish_run_id = uuid4()

        # Start parent agent chain
        handler.on_chain_start(
            serialized={"name": "AgentExecutor"},
            inputs={"input": "test"},
            run_id=parent_run_id,
        )

        # Record agent finish
        finish = MagicMock()
        finish.return_values = {"output": "4"}
        finish.log = "Final Answer: 4"

        handler.on_agent_finish(
            finish=finish,
            run_id=finish_run_id,
            parent_run_id=parent_run_id,
        )

        # Check finish was recorded in parent span
        parent_span = handler._runs[str(parent_run_id)]["span"]
        assert "agent.finish" in parent_span.attributes

    def test_defensive_error_handling(self, handler, mock_client):
        """Test that handler doesn't crash on errors."""
        # Try to end a run that doesn't exist - should not raise
        handler.on_chain_end(outputs={}, run_id=uuid4())

        # Try to error a run that doesn't exist - should not raise
        handler.on_chain_error(error=ValueError("test"), run_id=uuid4())

        # Handler should still be functional
        run_id = uuid4()
        handler.on_chain_start(
            serialized={"name": "TestChain"},
            inputs={},
            run_id=run_id,
        )
        assert str(run_id) in handler._runs

    def test_extract_component_type(self, handler):
        """Test component type extraction from serialized data."""
        # Test with name
        serialized = {"name": "ChatOpenAI"}
        assert handler._extract_component_type(serialized) == "ChatOpenAI"

        # Test with id list
        serialized = {"id": ["langchain", "chains", "RetrievalQA"]}
        assert handler._extract_component_type(serialized) == "RetrievalQA"

        # Test with unknown format
        serialized = {}
        assert handler._extract_component_type(serialized) == "Unknown"

    def test_nested_tool_and_function_spans(self, handler, mock_client):
        """Test that @trace decorated functions create nested spans under tool spans."""
        from lumenova_beacon import trace
        from lumenova_beacon.tracing.trace import get_current_span

        tool_run_id = uuid4()

        # Start tool span (simulating LangChain's on_tool_start)
        handler.on_tool_start(
            serialized={"name": "TestTool"},
            input_str="test input",
            run_id=tool_run_id,
        )

        # Verify tool span is set as current
        tool_span = handler._runs[str(tool_run_id)]["span"]
        current_span = get_current_span()
        assert current_span == tool_span
        assert tool_span.span_type == SpanType.TOOL

        # Simulate @trace decorated function executing inside the tool
        @trace()
        def tool_implementation(x: int) -> int:
            """Simulated tool function with @trace decorator."""
            return x * 2

        result = tool_implementation(5)
        assert result == 10

        # The @trace decorator should have created a function span
        # and it should have been sent when the function completed
        assert mock_client.export_span.call_count >= 1

        # Get the function span (should be the first call)
        function_span = mock_client.export_span.call_args_list[0][0][0]

        # Verify function span properties
        assert function_span.span_type == SpanType.FUNCTION
        assert function_span.name == "tool_implementation"
        assert function_span.parent_id == tool_span.span_id
        assert function_span.trace_id == tool_span.trace_id

        # End tool span
        handler.on_tool_end(output="test output", run_id=tool_run_id)

        # Verify tool span was sent
        assert mock_client.export_span.call_count >= 2
        sent_tool_span = mock_client.export_span.call_args_list[-1][0][0]
        assert sent_tool_span.span_type == SpanType.TOOL

    def test_context_restoration_after_tool_completion(self, handler, mock_client):
        """Test that span context is properly restored after tool completion."""
        from lumenova_beacon.tracing.trace import get_current_span

        parent_run_id = uuid4()
        tool_run_id = uuid4()

        # Start parent chain
        handler.on_chain_start(
            serialized={"name": "ParentChain"},
            inputs={"query": "test"},
            run_id=parent_run_id,
        )

        parent_span = handler._runs[str(parent_run_id)]["span"]
        assert get_current_span() == parent_span

        # Start tool (child of chain)
        handler.on_tool_start(
            serialized={"name": "TestTool"},
            input_str="test",
            run_id=tool_run_id,
            parent_run_id=parent_run_id,
        )

        tool_span = handler._runs[str(tool_run_id)]["span"]
        assert get_current_span() == tool_span
        assert tool_span.parent_id == parent_span.span_id

        # End tool
        handler.on_tool_end(output="result", run_id=tool_run_id)

        # Context should be restored to parent
        assert get_current_span() == parent_span

        # End parent
        handler.on_chain_end(outputs={"result": "done"}, run_id=parent_run_id)

    def test_context_restoration_on_error(self, handler, mock_client):
        """Test that span context is properly restored even when tool errors."""
        from lumenova_beacon.tracing.trace import get_current_span

        parent_run_id = uuid4()
        tool_run_id = uuid4()

        # Start parent chain
        handler.on_chain_start(
            serialized={"name": "ParentChain"},
            inputs={"query": "test"},
            run_id=parent_run_id,
        )

        parent_span = handler._runs[str(parent_run_id)]["span"]

        # Start tool
        handler.on_tool_start(
            serialized={"name": "TestTool"},
            input_str="test",
            run_id=tool_run_id,
            parent_run_id=parent_run_id,
        )

        # Tool errors
        error = ValueError("Tool failed")
        handler.on_tool_error(error=error, run_id=tool_run_id, parent_run_id=parent_run_id)

        # Context should be restored to parent even after error
        assert get_current_span() == parent_span

        # End parent
        handler.on_chain_end(outputs={"result": "done"}, run_id=parent_run_id)

    def test_multiple_nested_function_calls_in_tool(self, handler, mock_client):
        """Test multiple @trace decorated functions within a single tool."""
        from lumenova_beacon import trace

        tool_run_id = uuid4()

        # Start tool span
        handler.on_tool_start(
            serialized={"name": "ComplexTool"},
            input_str="test",
            run_id=tool_run_id,
        )

        tool_span = handler._runs[str(tool_run_id)]["span"]

        # Define multiple traced helper functions
        @trace()
        def helper1(x: int) -> int:
            return x + 1

        @trace()
        def helper2(x: int) -> int:
            return x * 2

        # Execute them
        result1 = helper1(5)
        result2 = helper2(result1)

        assert result1 == 6
        assert result2 == 12

        # Both function spans should have been sent
        # Each should have the tool span as parent and share trace_id
        function_calls = [call for call in mock_client.export_span.call_args_list]
        assert len(function_calls) >= 2

        # Check both function spans
        helper1_span = function_calls[0][0][0]
        helper2_span = function_calls[1][0][0]

        assert helper1_span.span_type == SpanType.FUNCTION
        assert helper1_span.parent_id == tool_span.span_id
        assert helper1_span.trace_id == tool_span.trace_id

        assert helper2_span.span_type == SpanType.FUNCTION
        assert helper2_span.parent_id == tool_span.span_id
        assert helper2_span.trace_id == tool_span.trace_id

        # End tool
        handler.on_tool_end(output="done", run_id=tool_run_id)

    def test_context_cleared_after_root_langchain_span(self, handler, mock_client):
        """Test that context is cleared after root LangChain span completes.

        This prevents subsequent @trace calls from incorrectly nesting under
        the completed LangChain span.
        """
        from lumenova_beacon import trace
        from lumenova_beacon.tracing.trace import get_current_span

        # Execute a root LangChain chain (no parent)
        chain_run_id = uuid4()
        handler.on_chain_start(
            serialized={"name": "RootChain"},
            inputs={"query": "test"},
            run_id=chain_run_id,
        )

        chain_span = handler._runs[str(chain_run_id)]["span"]
        assert get_current_span() == chain_span

        # End the chain
        handler.on_chain_end(outputs={"result": "done"}, run_id=chain_run_id)

        # Context should be cleared (no current span)
        assert get_current_span() is None

        # Now trace a completely separate function
        @trace()
        def separate_function() -> str:
            return "independent"

        result = separate_function()
        assert result == "independent"

        # Get the function span (should be sent to mock_client)
        function_span = mock_client.export_span.call_args_list[-1][0][0]

        # Verify the function span is NOT a child of the chain span
        assert function_span.span_type == SpanType.FUNCTION
        assert function_span.name == "separate_function"
        assert function_span.parent_id is None  # No parent!
        assert function_span.trace_id != chain_span.trace_id  # Different trace!


class TestBeaconCallbackHandlerMetadata:
    """Test suite for BeaconCallbackHandler metadata functionality."""

    def test_init_with_environment(self):
        """Test initialization with environment parameter."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            mock_client = MagicMock(spec=BeaconClient)
            mock_client.config.session_id = None
            mock_get.return_value = mock_client
            handler = BeaconCallbackHandler(environment="production")
            assert handler._environment == "production"

    def test_init_with_agent_name(self):
        """Test initialization with agent_name parameter."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            mock_client = MagicMock(spec=BeaconClient)
            mock_client.config.session_id = None
            mock_get.return_value = mock_client
            handler = BeaconCallbackHandler(agent_name="my-agent")
            assert handler._agent_name == "my-agent"

    def test_init_with_metadata(self):
        """Test initialization with custom metadata dict."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            mock_client = MagicMock(spec=BeaconClient)
            mock_client.config.session_id = None
            mock_get.return_value = mock_client
            handler = BeaconCallbackHandler(
                metadata={"app_name": "my-app", "version": "1.0.0"}
            )
            assert handler._metadata == {"app_name": "my-app", "version": "1.0.0"}

    def test_init_with_all_new_parameters(self):
        """Test initialization with all new metadata parameters."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            mock_client = MagicMock(spec=BeaconClient)
            mock_client.config.session_id = None
            mock_get.return_value = mock_client
            handler = BeaconCallbackHandler(
                session_id="test-session",
                environment="staging",
                agent_name="test-agent",
                metadata={"team": "platform", "priority": 1}
            )
            assert handler._session_id == "test-session"
            assert handler._environment == "staging"
            assert handler._agent_name == "test-agent"
            assert handler._metadata == {"team": "platform", "priority": 1}

    def test_metadata_defaults_to_empty_dict(self):
        """Test that metadata defaults to empty dict when not provided."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            mock_client = MagicMock(spec=BeaconClient)
            mock_client.config.session_id = None
            mock_get.return_value = mock_client
            handler = BeaconCallbackHandler()
            assert handler._metadata == {}

    def test_environment_attribute_set_on_span(self):
        """Test that environment is set as span attribute."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            with patch("lumenova_beacon.tracing.integrations.langchain.trace") as mock_trace:
                mock_client = MagicMock(spec=BeaconClient)
                mock_client.config.session_id = None
                mock_get.return_value = mock_client

                mock_span = MagicMock()
                mock_tracer = MagicMock()
                mock_tracer.start_span.return_value = mock_span
                mock_trace.get_tracer.return_value = mock_tracer
                mock_trace.set_span_in_context.return_value = MagicMock()

                handler = BeaconCallbackHandler(environment="production")

                run_id = uuid4()
                handler.on_chain_start(
                    serialized={"name": "TestChain"},
                    inputs={"query": "test"},
                    run_id=run_id,
                )

                # Verify environment attribute was set (OTEL standard)
                mock_span.set_attribute.assert_any_call("deployment.environment.name", "production")

    def test_agent_name_attribute_set_on_span(self):
        """Test that agent_name is set as span attribute."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            with patch("lumenova_beacon.tracing.integrations.langchain.trace") as mock_trace:
                mock_client = MagicMock(spec=BeaconClient)
                mock_client.config.session_id = None
                mock_get.return_value = mock_client

                mock_span = MagicMock()
                mock_tracer = MagicMock()
                mock_tracer.start_span.return_value = mock_span
                mock_trace.get_tracer.return_value = mock_tracer
                mock_trace.set_span_in_context.return_value = MagicMock()

                handler = BeaconCallbackHandler(agent_name="my-agent")

                run_id = uuid4()
                handler.on_chain_start(
                    serialized={"name": "TestChain"},
                    inputs={"query": "test"},
                    run_id=run_id,
                )

                # Verify agent_name attribute was set (OTEL standard)
                mock_span.set_attribute.assert_any_call("gen_ai.agent.name", "my-agent")

    def test_custom_metadata_attributes_set_on_span(self):
        """Test that custom metadata dict values are set as span attributes."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            with patch("lumenova_beacon.tracing.integrations.langchain.trace") as mock_trace:
                mock_client = MagicMock(spec=BeaconClient)
                mock_client.config.session_id = None
                mock_get.return_value = mock_client

                mock_span = MagicMock()
                mock_tracer = MagicMock()
                mock_tracer.start_span.return_value = mock_span
                mock_trace.get_tracer.return_value = mock_tracer
                mock_trace.set_span_in_context.return_value = MagicMock()

                handler = BeaconCallbackHandler(
                    metadata={"app_name": "my-app", "version": "1.0.0", "count": 42}
                )

                run_id = uuid4()
                handler.on_chain_start(
                    serialized={"name": "TestChain"},
                    inputs={"query": "test"},
                    run_id=run_id,
                )

                # Verify custom metadata attributes were set with beacon.metadata. prefix
                mock_span.set_attribute.assert_any_call("beacon.metadata.app_name", "my-app")
                mock_span.set_attribute.assert_any_call("beacon.metadata.version", "1.0.0")
                mock_span.set_attribute.assert_any_call("beacon.metadata.count", 42)

    def test_complex_metadata_value_json_serialized(self):
        """Test that complex metadata values are JSON serialized."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            with patch("lumenova_beacon.tracing.integrations.langchain.trace") as mock_trace:
                mock_client = MagicMock(spec=BeaconClient)
                mock_client.config.session_id = None
                mock_get.return_value = mock_client

                mock_span = MagicMock()
                mock_tracer = MagicMock()
                mock_tracer.start_span.return_value = mock_span
                mock_trace.get_tracer.return_value = mock_tracer
                mock_trace.set_span_in_context.return_value = MagicMock()

                handler = BeaconCallbackHandler(
                    metadata={"tags": ["tag1", "tag2"], "config": {"key": "value"}}
                )

                run_id = uuid4()
                handler.on_chain_start(
                    serialized={"name": "TestChain"},
                    inputs={"query": "test"},
                    run_id=run_id,
                )

                # Verify complex values are JSON serialized
                import json
                mock_span.set_attribute.assert_any_call(
                    "beacon.metadata.tags", json.dumps(["tag1", "tag2"])
                )
                mock_span.set_attribute.assert_any_call(
                    "beacon.metadata.config", json.dumps({"key": "value"})
                )

    def test_langgraph_graph_name_extraction(self):
        """Test that graph name is extracted from LangGraph metadata when agent_name not set."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            with patch("lumenova_beacon.tracing.integrations.langchain.trace") as mock_trace:
                mock_client = MagicMock(spec=BeaconClient)
                mock_client.config.session_id = None
                mock_get.return_value = mock_client

                mock_span = MagicMock()
                mock_tracer = MagicMock()
                mock_tracer.start_span.return_value = mock_span
                mock_trace.get_tracer.return_value = mock_tracer
                mock_trace.set_span_in_context.return_value = MagicMock()

                # No agent_name set - should extract from LangGraph metadata
                handler = BeaconCallbackHandler()

                run_id = uuid4()
                handler.on_chain_start(
                    serialized={"name": "TestChain"},
                    inputs={"query": "test"},
                    run_id=run_id,
                    metadata={"langgraph_checkpoint_ns": "my_graph_name"},
                )

                # Verify graph name was extracted and set (OTEL standard)
                mock_span.set_attribute.assert_any_call("gen_ai.agent.name", "my_graph_name")

    def test_agent_name_not_overridden_by_langgraph(self):
        """Test that explicit agent_name is not overridden by LangGraph metadata."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            with patch("lumenova_beacon.tracing.integrations.langchain.trace") as mock_trace:
                mock_client = MagicMock(spec=BeaconClient)
                mock_client.config.session_id = None
                mock_get.return_value = mock_client

                mock_span = MagicMock()
                mock_tracer = MagicMock()
                mock_tracer.start_span.return_value = mock_span
                mock_trace.get_tracer.return_value = mock_tracer
                mock_trace.set_span_in_context.return_value = MagicMock()

                # Explicit agent_name set - should NOT be overridden
                handler = BeaconCallbackHandler(agent_name="my-explicit-agent")

                run_id = uuid4()
                handler.on_chain_start(
                    serialized={"name": "TestChain"},
                    inputs={"query": "test"},
                    run_id=run_id,
                    metadata={"langgraph_checkpoint_ns": "graph_name_from_langgraph"},
                )

                # Verify explicit agent_name was used (set in _start_span) (OTEL standard)
                mock_span.set_attribute.assert_any_call("gen_ai.agent.name", "my-explicit-agent")

                # Verify graph name was NOT set (no second call with graph name)
                calls = [call for call in mock_span.set_attribute.call_args_list
                         if call[0][0] == "gen_ai.agent.name"]
                assert len(calls) == 1
                assert calls[0][0][1] == "my-explicit-agent"

    def test_agent_id_attribute_set_on_span(self):
        """Test that agent_id is set as span attribute."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            with patch("lumenova_beacon.tracing.integrations.langchain.trace") as mock_trace:
                mock_client = MagicMock(spec=BeaconClient)
                mock_client.config.session_id = None
                mock_get.return_value = mock_client

                mock_span = MagicMock()
                mock_tracer = MagicMock()
                mock_tracer.start_span.return_value = mock_span
                mock_trace.get_tracer.return_value = mock_tracer
                mock_trace.set_span_in_context.return_value = MagicMock()

                handler = BeaconCallbackHandler(agent_id="agent-001")

                run_id = uuid4()
                handler.on_chain_start(
                    serialized={"name": "TestChain"},
                    inputs={"query": "test"},
                    run_id=run_id,
                )

                # Verify agent_id attribute was set (OTEL standard)
                mock_span.set_attribute.assert_any_call("gen_ai.agent.id", "agent-001")

    def test_agent_description_attribute_set_on_span(self):
        """Test that agent_description is set as span attribute."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            with patch("lumenova_beacon.tracing.integrations.langchain.trace") as mock_trace:
                mock_client = MagicMock(spec=BeaconClient)
                mock_client.config.session_id = None
                mock_get.return_value = mock_client

                mock_span = MagicMock()
                mock_tracer = MagicMock()
                mock_tracer.start_span.return_value = mock_span
                mock_trace.get_tracer.return_value = mock_tracer
                mock_trace.set_span_in_context.return_value = MagicMock()

                handler = BeaconCallbackHandler(agent_description="A helpful assistant")

                run_id = uuid4()
                handler.on_chain_start(
                    serialized={"name": "TestChain"},
                    inputs={"query": "test"},
                    run_id=run_id,
                )

                # Verify agent_description attribute was set (OTEL standard)
                mock_span.set_attribute.assert_any_call("gen_ai.agent.description", "A helpful assistant")

    def test_model_parameters_extracted_on_llm_start(self):
        """Test that model parameters are extracted and set on LLM spans."""
        with patch("lumenova_beacon.integrations.langchain.get_client") as mock_get:
            with patch("lumenova_beacon.tracing.integrations.langchain.trace") as mock_trace:
                mock_client = MagicMock(spec=BeaconClient)
                mock_client.config.session_id = None
                mock_get.return_value = mock_client

                mock_span = MagicMock()
                mock_tracer = MagicMock()
                mock_tracer.start_span.return_value = mock_span
                mock_trace.get_tracer.return_value = mock_tracer
                mock_trace.set_span_in_context.return_value = MagicMock()

                handler = BeaconCallbackHandler()

                run_id = uuid4()
                serialized = {
                    "name": "ChatOpenAI",
                    "kwargs": {
                        "model_name": "gpt-4",
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 1000,
                    }
                }

                handler.on_llm_start(
                    serialized=serialized,
                    prompts=["Hello"],
                    run_id=run_id,
                )

                # Verify model parameters were set (OTEL standard)
                mock_span.set_attribute.assert_any_call("gen_ai.request.temperature", 0.7)
                mock_span.set_attribute.assert_any_call("gen_ai.request.top_p", 0.9)
                mock_span.set_attribute.assert_any_call("gen_ai.request.max_tokens", 1000)
