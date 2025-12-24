"""
Comprehensive unit tests for the error handling system.

Tests the new exception hierarchy, API error classification,
retry logic, and error routing functionality.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, Optional

# Import exceptions
from marsys.agents.exceptions import (
    # Base exceptions
    AgentFrameworkError,
    MessageError,
    ModelError,

    # API error classification
    APIErrorClassification,
    ModelAPIError,

    # Coordination errors
    CoordinationError,
    TopologyError,
    BranchExecutionError,
    ParallelExecutionError,

    # State errors
    StateError,
    SessionNotFoundError,
    CheckpointError,
    StateCorruptionError,
    StateLockError,

    # Resource errors
    ResourceError,
    PoolExhaustedError,
    TimeoutError,

    # Communication errors
    CommunicationError,

    # Workflow errors
    WorkflowError,

    # Browser errors
    BrowserError,
    BrowserNotInitializedError,
    BrowserConnectionError,

    # Tool errors
    ToolExecutionError,
    ActionValidationError,
)

# Import components
from marsys.coordination.execution.step_executor import StepExecutor
from marsys.coordination.routing.router import Router
from marsys.coordination.routing.types import StepType, RoutingContext, RoutingDecision
from marsys.coordination.status.events import CriticalErrorEvent, ResourceLimitEvent
from marsys.models.models import OpenAIAdapter, AnthropicAdapter, GoogleAdapter, OpenRouterAdapter
from marsys.models.response_models import ErrorResponse


class TestExceptionHierarchy:
    """Test the new exception hierarchy and inheritance."""

    def test_base_exception_creation(self):
        """Test creating base exceptions with context."""
        error = AgentFrameworkError(
            "Test error",
            error_code="TEST_ERROR",
            context={"key": "value"},
            user_message="User friendly message",
            suggestion="Try this fix"
        )

        assert "Test error" in str(error)
        assert error.error_code == "TEST_ERROR"
        assert error.context == {"key": "value"}
        assert error.user_message == "User friendly message"
        assert error.suggestion == "Try this fix"

    def test_topology_error(self):
        """Test TopologyError with specific context."""
        error = TopologyError(
            "Invalid topology",
            topology_issue="no_entry_agents",
            affected_nodes=["Agent1", "Agent2"]
        )

        assert error.topology_issue == "no_entry_agents"
        assert error.affected_nodes == ["Agent1", "Agent2"]
        assert error.error_code == "TOPOLOGY_ERROR"

    def test_pool_exhausted_error(self):
        """Test PoolExhaustedError with pool context."""
        error = PoolExhaustedError(
            "No available instances",
            pool_name="test_pool",
            total_instances=5
        )

        assert error.pool_name == "test_pool"
        assert error.total_instances == 5
        assert error.error_code == "POOL_EXHAUSTED_ERROR"


class TestAPIErrorClassification:
    """Test API error classification and detection."""

    def test_insufficient_credits_detection(self):
        """Test detection of insufficient credits errors."""
        # OpenAI insufficient quota
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"type": "insufficient_quota"}}
        mock_response.headers = {}

        error = ModelAPIError.from_provider_response(
            provider="openai",
            response=mock_response,
            exception=None
        )
        assert error.classification == APIErrorClassification.INSUFFICIENT_CREDITS.value
        assert error.is_critical()

        # Anthropic credit balance
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Your credit balance is insufficient"}}

        error = ModelAPIError.from_provider_response(
            provider="anthropic",
            response=mock_response,
            exception=None
        )
        assert error.classification == APIErrorClassification.INSUFFICIENT_CREDITS.value
        assert error.is_critical()

    def test_rate_limit_detection(self):
        """Test detection of rate limit errors."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"type": "rate_limit"}}
        mock_response.headers = {"retry-after": "60"}

        error = ModelAPIError.from_provider_response(
            provider="openai",
            response=mock_response,
            exception=Exception("Rate limit exceeded")
        )
        assert error.classification == APIErrorClassification.RATE_LIMIT.value
        assert not error.is_critical()
        assert error.is_retryable

    def test_authentication_error_detection(self):
        """Test detection of authentication errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"type": "authentication_error"}}

        error = ModelAPIError.from_provider_response(
            provider="anthropic",
            response=mock_response,
            exception=None
        )
        assert error.classification == APIErrorClassification.AUTHENTICATION_FAILED.value
        assert error.is_critical()

    def test_provider_specific_suggestions(self):
        """Test provider-specific error suggestions."""
        # OpenAI credits
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"type": "insufficient_quota"}}
        mock_response.headers = {}

        error = ModelAPIError.from_provider_response(
            provider="openai",
            response=mock_response,
            exception=None
        )
        # The generated suggested_action is in the constructor
        assert error.is_critical()
        assert error.classification == APIErrorClassification.INSUFFICIENT_CREDITS.value

        # Anthropic credits
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Your credit balance is insufficient"}}

        error = ModelAPIError.from_provider_response(
            provider="anthropic",
            response=mock_response,
            exception=None
        )
        assert error.is_critical()
        assert error.classification == APIErrorClassification.INSUFFICIENT_CREDITS.value


class TestProviderAdapters:
    """Test provider adapter error handling."""

    @pytest.fixture
    def mock_logger(self):
        with patch('src.models.models.logger') as mock:
            yield mock

    def test_openai_adapter_critical_error(self, mock_logger):
        """Test OpenAI adapter raises on critical errors."""
        adapter = OpenAIAdapter(api_key="test_key")

        # Mock insufficient quota error
        error = Exception("insufficient_quota")
        error.response = Mock(status_code=429, json=lambda: {"error": {"code": "insufficient_quota"}})

        with pytest.raises(ModelAPIError) as exc_info:
            adapter.handle_api_error(error, error.response)

        assert exc_info.value.is_critical()
        assert exc_info.value.classification == APIErrorClassification.INSUFFICIENT_CREDITS.value

    def test_anthropic_adapter_payment_required(self, mock_logger):
        """Test Anthropic adapter handles payment required."""
        adapter = AnthropicAdapter(api_key="test_key")

        # Mock credit balance error
        error = Exception("credit balance")
        response = {"error": {"message": "Your credit balance is insufficient"}}

        with pytest.raises(ModelAPIError) as exc_info:
            adapter.handle_api_error(error, response)

        assert exc_info.value.is_critical()
        assert "console.anthropic.com" in exc_info.value.suggested_action

    def test_google_adapter_resource_exhausted(self, mock_logger):
        """Test Google adapter handles resource exhausted."""
        adapter = GoogleAdapter(api_key="test_key")

        # Mock resource exhausted error
        error = Exception("RESOURCE_EXHAUSTED")
        error.message = "Quota exceeded"

        with pytest.raises(ModelAPIError) as exc_info:
            adapter.handle_api_error(error, None)

        assert exc_info.value.classification == APIErrorClassification.INSUFFICIENT_CREDITS.value

    def test_openrouter_adapter_payment_required(self, mock_logger):
        """Test OpenRouter adapter handles 402 payment required."""
        adapter = OpenRouterAdapter(api_key="test_key")

        # Mock 402 error
        error = Exception("Payment required")
        error.response = Mock(status_code=402)

        with pytest.raises(ModelAPIError) as exc_info:
            adapter.handle_api_error(error, error.response)

        assert exc_info.value.is_critical()
        assert exc_info.value.classification == APIErrorClassification.INSUFFICIENT_CREDITS.value


class TestStepExecutorErrorHandling:
    """Test StepExecutor error handling methods."""

    @pytest.fixture
    async def step_executor(self):
        """Create a StepExecutor instance for testing."""
        with patch('src.coordination.execution.step_executor.StatusManager'):
            executor = StepExecutor(
                topology_graph=Mock(),
                agent_registry=Mock(),
                context_manager=Mock(),
                status_manager=Mock(),
                memory_manager=Mock()
            )
            return executor

    @pytest.mark.asyncio
    async def test_handle_model_api_error_critical(self, step_executor):
        """Test handling of critical API errors."""
        error = ModelAPIError(
            "Insufficient credits",
            provider="openai",
            classification=APIErrorClassification.INSUFFICIENT_CREDITS.value,
            suggested_action="Add credits"
        )

        # Mock the notification method
        step_executor._notify_critical_error = AsyncMock()

        result = await step_executor._handle_model_api_error(
            error, "TestAgent", {}, 1
        )

        # Should notify and not retry
        step_executor._notify_critical_error.assert_called_once()
        assert result is None  # No retry for critical errors

    @pytest.mark.asyncio
    async def test_handle_pool_exhausted_limited_retries(self, step_executor):
        """Test limited retries for pool exhausted errors."""
        error = PoolExhaustedError(
            "No instances available",
            pool_name="test_pool",
            total_instances=3
        )

        # First retry should wait and retry
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await step_executor._handle_pool_exhausted_error(
                error, "TestAgent", {}, 0
            )
            assert result == "retry"

        # Third retry should give up
        result = await step_executor._handle_pool_exhausted_error(
            error, "TestAgent", {}, 2
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_timeout_no_retry(self, step_executor):
        """Test timeout errors are not retried."""
        error = TimeoutError(
            "Operation timed out",
            timeout_seconds=30,
            operation="agent_execution"
        )

        result = await step_executor._handle_timeout_error(
            error, "TestAgent", {}, 0
        )

        assert result is None  # No retry for timeouts

    @pytest.mark.asyncio
    async def test_notify_critical_error_event(self, step_executor):
        """Test critical error notification via events."""
        error = ModelAPIError(
            "API Error",
            provider="anthropic",
            classification=APIErrorClassification.INSUFFICIENT_CREDITS.value,
            suggested_action="Check billing"
        )

        # Mock status manager
        step_executor.status_manager.emit = AsyncMock()

        await step_executor._notify_critical_error(error, "TestAgent", {})

        # Verify event was emitted
        step_executor.status_manager.emit.assert_called_once()
        call_args = step_executor.status_manager.emit.call_args[0]
        event = call_args[0]

        assert isinstance(event, CriticalErrorEvent)
        assert event.error_type == APIErrorClassification.INSUFFICIENT_CREDITS.value
        assert event.provider == "anthropic"
        assert event.suggested_action == "Check billing"


class TestRouterErrorHandling:
    """Test Router error routing functionality."""

    @pytest.fixture
    def router(self):
        """Create a Router instance for testing."""
        topology_graph = Mock()
        topology_graph.agents = {"Agent1": Mock(), "Agent2": Mock(), "User": Mock()}

        return Router(
            topology_graph=topology_graph,
            context_manager=Mock()
        )

    def test_check_error_conditions_critical_api_error(self, router):
        """Test routing of critical API errors to User."""
        context = RoutingContext(
            current_agent="Agent1",
            previous_agent=None,
            task="Test task",
            response_content="Error occurred",
            metadata={
                "critical_api_error": True,
                "error_type": "insufficient_credits",
                "provider": "openai",
                "suggested_action": "Add credits"
            },
            current_branch_id="branch1",
            conversation_history=[],
            branch_agents=["Agent1"]
        )

        decision = router._check_error_conditions(context)

        assert decision is not None
        assert decision.next_agent == "User"
        assert decision.step_type == StepType.ERROR_NOTIFICATION
        assert decision.metadata["error_details"]["type"] == "insufficient_credits"

    def test_check_error_conditions_pool_exhausted(self, router):
        """Test routing of pool exhaustion errors."""
        context = RoutingContext(
            current_agent="Agent1",
            previous_agent=None,
            task="Test task",
            response_content="Pool exhausted",
            metadata={
                "pool_exhausted": True,
                "pool_name": "agent_pool",
                "total_instances": 5,
                "wait_time": 30
            },
            current_branch_id="branch1",
            conversation_history=[],
            branch_agents=["Agent1"]
        )

        decision = router._check_error_conditions(context)

        assert decision is not None
        assert decision.next_agent == "User"
        assert decision.step_type == StepType.RESOURCE_NOTIFICATION
        assert decision.metadata["resource_info"]["pool_name"] == "agent_pool"

    def test_check_error_conditions_timeout(self, router):
        """Test routing of timeout errors."""
        context = RoutingContext(
            current_agent="Agent1",
            previous_agent=None,
            task="Test task",
            response_content="Operation timed out",
            metadata={
                "timeout_error": True,
                "timeout_seconds": 60,
                "operation": "agent_execution"
            },
            current_branch_id="branch1",
            conversation_history=[],
            branch_agents=["Agent1"]
        )

        decision = router._check_error_conditions(context)

        assert decision is not None
        assert decision.next_agent == "User"
        assert decision.step_type == StepType.COMPLETION
        assert "timed out" in decision.metadata["completion_reason"]


class TestBrowserExceptions:
    """Test browser-specific exceptions."""

    def test_browser_not_initialized_error(self):
        """Test BrowserNotInitializedError creation."""
        error = BrowserNotInitializedError(operation="take_screenshot")

        assert error.operation == "take_screenshot"
        assert "take_screenshot" in str(error)
        assert error.error_code == "BROWSER_NOT_INITIALIZED_ERROR"

    def test_browser_connection_error(self):
        """Test BrowserConnectionError with install command."""
        error = BrowserConnectionError(
            "Missing dependencies",
            browser_type="playwright",
            install_command="playwright install chromium"
        )

        assert error.browser_type == "playwright"
        assert error.install_command == "playwright install chromium"
        assert "playwright install chromium" in error.suggestion

    def test_action_validation_error(self):
        """Test ActionValidationError for invalid parameters."""
        error = ActionValidationError(
            "Invalid selector",
            action_name="click",
            invalid_params={"selector": None, "role": None}
        )

        assert error.action_name == "click"
        assert error.invalid_params == {"selector": None, "role": None}
        assert error.error_code == "ACTION_VALIDATION_ERROR"


class TestToolExecutionErrors:
    """Test tool execution error handling."""

    def test_tool_execution_error(self):
        """Test ToolExecutionError with tool context."""
        error = ToolExecutionError(
            "Tool failed",
            tool_name="web_search",
            tool_args={"query": "test"},
            execution_error="Network error"
        )

        assert error.tool_name == "web_search"
        assert error.tool_args == {"query": "test"}
        assert error.execution_error == "Network error"
        assert error.error_code == "TOOL_EXECUTION_ERROR"


class TestIntegrationScenarios:
    """Test end-to-end error handling scenarios."""

    @pytest.mark.asyncio
    async def test_api_error_flow(self):
        """Test complete flow from API error to user notification."""
        # This would require more complex setup with actual components
        # For now, we verify the pieces work together conceptually

        # 1. API error occurs
        error = ModelAPIError.from_provider_response(
            provider="openai",
            response={"error": {"code": "insufficient_quota"}},
            exception=None
        )

        # 2. Error is critical
        assert error.is_critical()

        # 3. Would trigger notification
        assert error.suggested_action is not None
        assert "platform.openai.com" in error.suggested_action

    def test_error_chain_preservation(self):
        """Test that error chains are preserved."""
        original = ValueError("Original error")

        try:
            raise TopologyError(
                "Topology validation failed",
                topology_issue="invalid_edges"
            ) from original
        except TopologyError as e:
            assert e.__cause__ == original
            assert "Original error" in str(e.__cause__)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])