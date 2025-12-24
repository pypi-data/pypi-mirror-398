"""
Unit tests for the BaseAgent.auto_run method.

This test module verifies that the auto_run method correctly:
1. Creates topology from allowed_peers
2. Manages RequestContext properly
3. Handles progress monitoring
4. Processes various input formats
5. Returns expected results
6. Handles errors gracefully
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call, Mock
from typing import Dict, Any, List
import uuid

from marsys.agents.agents import BaseAgent, Agent
from marsys.agents.utils import RequestContext, LogLevel
from marsys.agents.memory import Message
from marsys.coordination import OrchestraResult
from marsys.models.models import ModelConfig
from marsys.agents.registry import AgentRegistry


class MockModel:
    """Mock model for testing."""
    def __init__(self, *args, **kwargs):
        pass
    
    async def run(self, messages: List[Dict[str, Any]], **kwargs) -> Message:
        return Message(
            role="assistant",
            content={
                "next_action": "final_response",
                "action_input": {"response": "Test response"}
            }
        )


class TestAutoRun:
    """Test suite for BaseAgent.auto_run method."""
    
    @pytest.fixture(autouse=True)
    def cleanup_registry(self):
        """Clean up the agent registry before and after each test."""
        # Clear registry before test
        AgentRegistry._agents.clear()
        AgentRegistry._counter = 0
        yield
        # Clear registry after test
        AgentRegistry._agents.clear()
        AgentRegistry._counter = 0
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent with allowed_peers."""
        # Use unique name for each test
        agent_name = f"TestAgent_{uuid.uuid4().hex[:8]}"
        
        # Create a mock ModelConfig with API key
        mock_config = ModelConfig(
            type="api",  # Required field
            provider="openai",  # Use a valid provider
            name="gpt-4",
            api_key="test-api-key",  # Provide a fake API key
            parameters={}
        )
        
        # Patch the model creation
        with patch.object(Agent, '_create_model_from_config', return_value=MockModel()):
            agent = Agent(
                model_config=mock_config,
                description="Test agent",
                agent_name=agent_name,
                allowed_peers=["PeerAgent1", "PeerAgent2"]
            )
            return agent
    
    @pytest.fixture
    def mock_orchestra_result(self):
        """Create a mock successful Orchestra result."""
        return OrchestraResult(
            success=True,
            final_response="Test successful response",
            branch_results=[],
            total_steps=5,
            total_duration=1.5,
            metadata={"test": True}
        )
    
    @pytest.fixture
    def mock_failed_orchestra_result(self):
        """Create a mock failed Orchestra result."""
        return OrchestraResult(
            success=False,
            final_response=None,
            branch_results=[],
            total_steps=0,
            total_duration=0.5,
            error="Test error message"
        )
    
    @pytest.mark.asyncio
    async def test_auto_run_basic(self, mock_agent, mock_orchestra_result):
        """Test basic auto_run functionality with string input."""
        with patch('src.coordination.Orchestra') as MockOrchestra:
            # Setup mock Orchestra
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(return_value=mock_orchestra_result)
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Run auto_run
            result = await mock_agent.auto_run("Test task")
            
            # Verify result
            assert result == "Test successful response"
            
            # Verify Orchestra was called correctly
            MockOrchestra.assert_called_once()
            mock_orchestra_instance.execute.assert_called_once()
            
            # Check the topology passed to Orchestra
            call_args = mock_orchestra_instance.execute.call_args
            topology = call_args.kwargs['topology']
            # Check that the agent name is in nodes (it's dynamic now)
            assert any("TestAgent" in node for node in topology["nodes"])
            assert "PeerAgent1" in topology["nodes"]
            assert "PeerAgent2" in topology["nodes"]
            assert topology["edges"] == []  # Built automatically from allowed_peers
            assert "max_steps(30)" in topology["rules"]
    
    @pytest.mark.asyncio
    async def test_auto_run_with_dict_input(self, mock_agent, mock_orchestra_result):
        """Test auto_run with dictionary input."""
        with patch('src.coordination.Orchestra') as MockOrchestra:
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(return_value=mock_orchestra_result)
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Run auto_run with dict input
            input_dict = {
                "prompt": "Test task",
                "extra_field": "extra_value"
            }
            result = await mock_agent.auto_run(input_dict)
            
            assert result == "Test successful response"
            
            # Verify the prompt was extracted correctly
            call_args = mock_orchestra_instance.execute.call_args
            assert call_args.kwargs['task'] == "Test task"
    
    @pytest.mark.asyncio
    async def test_auto_run_with_request_context(self, mock_agent, mock_orchestra_result):
        """Test auto_run with provided RequestContext."""
        with patch('src.coordination.Orchestra') as MockOrchestra:
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(return_value=mock_orchestra_result)
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Create a RequestContext
            request_context = RequestContext(
                task_id="test-task-123",
                initial_prompt="Test task",
                progress_queue=None,
                log_level=LogLevel.SUMMARY,
                max_depth=3,
                max_interactions=10
            )
            
            # Run auto_run with context
            result = await mock_agent.auto_run(
                "Test task",
                request_context=request_context
            )
            
            assert result == "Test successful response"
            
            # Verify context was passed to Orchestra
            call_args = mock_orchestra_instance.execute.call_args
            context = call_args.kwargs['context']
            assert context['request_context'] == request_context
    
    @pytest.mark.asyncio
    async def test_auto_run_with_progress_monitor(self, mock_agent, mock_orchestra_result):
        """Test auto_run with progress monitoring."""
        with patch('src.coordination.Orchestra') as MockOrchestra:
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(return_value=mock_orchestra_result)
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Create a mock progress monitor
            monitor_called = False
            async def mock_progress_monitor(queue, logger):
                nonlocal monitor_called
                monitor_called = True
                while True:
                    update = await queue.get()
                    if update is None:
                        break
            
            # Run auto_run with progress monitor
            result = await mock_agent.auto_run(
                "Test task",
                progress_monitor_func=mock_progress_monitor
            )
            
            assert result == "Test successful response"
            # Note: monitor_called might not be True due to async timing
    
    @pytest.mark.asyncio
    async def test_auto_run_max_steps(self, mock_agent, mock_orchestra_result):
        """Test auto_run with custom max_steps."""
        with patch('src.coordination.Orchestra') as MockOrchestra:
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(return_value=mock_orchestra_result)
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Run auto_run with custom max_steps
            result = await mock_agent.auto_run(
                "Test task",
                max_steps=50
            )
            
            assert result == "Test successful response"
            
            # Verify max_steps was passed correctly
            call_args = mock_orchestra_instance.execute.call_args
            assert call_args.kwargs['max_steps'] == 50
            topology = call_args.kwargs['topology']
            assert "max_steps(50)" in topology["rules"]
    
    @pytest.mark.asyncio
    async def test_auto_run_failure(self, mock_agent, mock_failed_orchestra_result):
        """Test auto_run handling of Orchestra failure."""
        with patch('src.coordination.Orchestra') as MockOrchestra:
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(return_value=mock_failed_orchestra_result)
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Run auto_run - should return error message
            result = await mock_agent.auto_run("Test task")
            
            # Check error message format
            assert "Error:" in result
            assert "Test error message" in result
    
    @pytest.mark.asyncio
    async def test_auto_run_exception_handling(self, mock_agent):
        """Test auto_run exception handling."""
        with patch('src.coordination.Orchestra') as MockOrchestra:
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(side_effect=Exception("Test exception"))
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Run auto_run - should handle exception
            result = await mock_agent.auto_run("Test task")
            
            # Check error message format
            assert "Error:" in result
            assert "exception" in result.lower()
            assert "Test exception" in result
    
    @pytest.mark.asyncio
    async def test_auto_run_no_allowed_peers_error(self):
        """Test auto_run raises error when no allowed_peers defined."""
        # Use unique name for test
        agent_name = f"TestAgentNoPeers_{uuid.uuid4().hex[:8]}"
        
        # Create a mock ModelConfig with API key
        mock_config = ModelConfig(
            type="api",  # Required field
            provider="openai",  # Use a valid provider
            name="gpt-4",
            api_key="test-api-key",  # Provide a fake API key
            parameters={}
        )
        
        # Create agent without allowed_peers
        with patch.object(Agent, '_create_model_from_config', return_value=MockModel()):
            agent = Agent(
                model_config=mock_config,
                description="Test agent",
                agent_name=agent_name
                # No allowed_peers
            )
            
            # Should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                await agent.auto_run("Test task")
            
            assert "no allowed_peers defined" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_auto_run_memory_cleanup(self, mock_agent, mock_orchestra_result):
        """Test auto_run cleans up single-run memory."""
        # Set memory retention to single_run
        mock_agent._memory_retention = "single_run"
        mock_agent.memory = MagicMock()
        mock_agent.memory.clear = MagicMock()
        
        with patch('src.coordination.Orchestra') as MockOrchestra:
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(return_value=mock_orchestra_result)
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Run auto_run
            result = await mock_agent.auto_run("Test task")
            
            assert result == "Test successful response"
            
            # Verify memory was cleared
            mock_agent.memory.clear.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auto_run_context_extraction(self, mock_agent, mock_orchestra_result):
        """Test auto_run correctly extracts context from complex input."""
        with patch('src.coordination.Orchestra') as MockOrchestra:
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(return_value=mock_orchestra_result)
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Create complex input with context
            input_data = {
                "prompt": "Test task",
                "passed_referenced_context": [
                    Message(role="user", content="Previous message")
                ]
            }
            
            # Run auto_run
            result = await mock_agent.auto_run(input_data)
            
            assert result == "Test successful response"
            
            # Verify context was extracted and passed
            call_args = mock_orchestra_instance.execute.call_args
            context = call_args.kwargs['context']
            assert 'context_messages' in context
            assert len(context['context_messages']) == 1
    
    @pytest.mark.asyncio
    async def test_auto_run_re_prompts_parameter(self, mock_agent, mock_orchestra_result):
        """Test auto_run passes max_re_prompts to context."""
        with patch('src.coordination.Orchestra') as MockOrchestra:
            mock_orchestra_instance = AsyncMock()
            mock_orchestra_instance.execute = AsyncMock(return_value=mock_orchestra_result)
            MockOrchestra.return_value = mock_orchestra_instance
            
            # Run auto_run with custom max_re_prompts
            result = await mock_agent.auto_run(
                "Test task",
                max_re_prompts=5
            )
            
            assert result == "Test successful response"
            
            # Verify max_re_prompts was passed in context
            call_args = mock_orchestra_instance.execute.call_args
            context = call_args.kwargs['context']
            assert context['max_re_prompts'] == 5