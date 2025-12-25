#!/usr/bin/env python
"""Integration tests for end-to-end broadcast communication flow."""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from massgen.agent_config import AgentConfig, CoordinationConfig
from massgen.backend.chat_completions import ChatCompletionsBackend
from massgen.chat_agent import SingleAgent
from massgen.orchestrator import Orchestrator
from massgen.broadcast.broadcast_dataclasses import BroadcastRequest
from datetime import datetime


@pytest.mark.asyncio
class TestBroadcastEndToEnd:
    """Test complete broadcast flow from creation to collection."""

    async def test_broadcast_lifecycle(self):
        """Test complete broadcast lifecycle: create -> inject -> respond -> collect."""
        # Setup
        config = AgentConfig.create_openai_config()
        config.coordination_config = CoordinationConfig(
            broadcast="agents",
            broadcast_timeout=300,
        )

        agent_a = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_a",
        )
        agent_b = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_b",
        )

        orchestrator = Orchestrator(
            agents={"agent_a": agent_a, "agent_b": agent_b},
            config=config,
        )

        # Step 1: Create broadcast
        request_id = await orchestrator.broadcast_channel.create_broadcast(
            sender_agent_id="agent_a",
            question="What is the capital of France?",
        )

        assert request_id in orchestrator.broadcast_channel.active_broadcasts

        # Step 2: Inject into agents
        await orchestrator.broadcast_channel.inject_into_agents(request_id)

        # Verify agent_b received it
        pending = await agent_b._check_broadcast_queue()
        assert pending is not None
        assert pending.question == "What is the capital of France?"

        # Step 3: Collect response
        await orchestrator.broadcast_channel.collect_response(
            request_id=request_id,
            responder_id="agent_b",
            content="The capital of France is Paris.",
        )

        # Step 4: Verify collection
        responses = orchestrator.broadcast_channel.get_broadcast_responses(request_id)
        assert responses["status"] == "complete"
        assert len(responses["responses"]) == 1
        assert responses["responses"][0]["content"] == "The capital of France is Paris."

    async def test_blocking_mode_broadcast(self):
        """Test broadcast in blocking mode (wait for responses)."""
        config = AgentConfig.create_openai_config()
        config.coordination_config = CoordinationConfig(
            broadcast="agents",
            broadcast_wait_by_default=True,
        )

        agent_a = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_a",
        )
        agent_b = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_b",
        )

        orchestrator = Orchestrator(
            agents={"agent_a": agent_a, "agent_b": agent_b},
            config=config,
        )

        # Create and inject broadcast
        request_id = await orchestrator.broadcast_channel.create_broadcast(
            sender_agent_id="agent_a",
            question="Test question",
        )
        await orchestrator.broadcast_channel.inject_into_agents(request_id)

        # Simulate agent_b responding in background
        async def respond_after_delay():
            await asyncio.sleep(0.1)
            await orchestrator.broadcast_channel.collect_response(
                request_id=request_id,
                responder_id="agent_b",
                content="Test answer",
            )

        respond_task = asyncio.create_task(respond_after_delay())

        # Wait for responses (blocking)
        result = await orchestrator.broadcast_channel.wait_for_responses(request_id, timeout=5)

        await respond_task  # Ensure background task completes

        assert result["status"] == "complete"
        assert len(result["responses"]) == 1

    async def test_polling_mode_broadcast(self):
        """Test broadcast in polling mode (check status later)."""
        config = AgentConfig.create_openai_config()
        config.coordination_config = CoordinationConfig(
            broadcast="agents",
            broadcast_wait_by_default=False,
        )

        agent_a = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_a",
        )
        agent_b = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_b",
        )

        orchestrator = Orchestrator(
            agents={"agent_a": agent_a, "agent_b": agent_b},
            config=config,
        )

        # Create and inject broadcast
        request_id = await orchestrator.broadcast_channel.create_broadcast(
            sender_agent_id="agent_a",
            question="Test question",
        )
        await orchestrator.broadcast_channel.inject_into_agents(request_id)

        # Check initial status (should be pending)
        status = orchestrator.broadcast_channel.get_broadcast_status(request_id)
        assert status["status"] == "collecting"
        assert status["response_count"] == 0

        # Collect response
        await orchestrator.broadcast_channel.collect_response(
            request_id=request_id,
            responder_id="agent_b",
            content="Test answer",
        )

        # Check final status
        status = orchestrator.broadcast_channel.get_broadcast_status(request_id)
        assert status["status"] == "complete"
        assert status["response_count"] == 1

        # Get responses
        responses = orchestrator.broadcast_channel.get_broadcast_responses(request_id)
        assert responses["status"] == "complete"
        assert len(responses["responses"]) == 1

    async def test_multiple_agents_responding(self):
        """Test broadcast with multiple agents responding."""
        config = AgentConfig.create_openai_config()
        config.coordination_config = CoordinationConfig(broadcast="agents")

        agent_a = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_a",
        )
        agent_b = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_b",
        )
        agent_c = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_c",
        )

        orchestrator = Orchestrator(
            agents={"agent_a": agent_a, "agent_b": agent_b, "agent_c": agent_c},
            config=config,
        )

        # Create broadcast from agent_a
        request_id = await orchestrator.broadcast_channel.create_broadcast(
            sender_agent_id="agent_a",
            question="What is 2+2?",
        )
        await orchestrator.broadcast_channel.inject_into_agents(request_id)

        # Both agent_b and agent_c should receive it
        pending_b = await agent_b._check_broadcast_queue()
        pending_c = await agent_c._check_broadcast_queue()

        assert pending_b is not None
        assert pending_c is not None

        # Both respond
        await orchestrator.broadcast_channel.collect_response(
            request_id, "agent_b", "4"
        )
        await orchestrator.broadcast_channel.collect_response(
            request_id, "agent_c", "2+2=4"
        )

        # Check all responses collected
        responses = orchestrator.broadcast_channel.get_broadcast_responses(request_id)
        assert responses["status"] == "complete"
        assert len(responses["responses"]) == 2

        response_contents = {r["responder_id"]: r["content"] for r in responses["responses"]}
        assert response_contents["agent_b"] == "4"
        assert response_contents["agent_c"] == "2+2=4"

    async def test_broadcast_timeout(self):
        """Test broadcast timeout when responses take too long."""
        config = AgentConfig.create_openai_config()
        config.coordination_config = CoordinationConfig(
            broadcast="agents",
            broadcast_timeout=1,  # 1 second timeout
        )

        agent_a = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_a",
        )
        agent_b = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_b",
        )

        orchestrator = Orchestrator(
            agents={"agent_a": agent_a, "agent_b": agent_b},
            config=config,
        )

        # Create broadcast
        request_id = await orchestrator.broadcast_channel.create_broadcast(
            sender_agent_id="agent_a",
            question="Test question",
            timeout=0.5,  # Very short timeout
        )
        await orchestrator.broadcast_channel.inject_into_agents(request_id)

        # Wait for responses (should timeout)
        result = await orchestrator.broadcast_channel.wait_for_responses(
            request_id,
            timeout=0.5,
        )

        assert result["status"] == "timeout"
        assert len(result["responses"]) == 0  # No responses in time

    async def test_coordination_tracker_integration(self):
        """Test that broadcasts are tracked in coordination tracker."""
        config = AgentConfig.create_openai_config()
        config.coordination_config = CoordinationConfig(broadcast="agents")

        agent_a = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_a",
        )
        agent_b = SingleAgent(
            backend=ChatCompletionsBackend(config=config.backend_params),
            agent_id="agent_b",
        )

        orchestrator = Orchestrator(
            agents={"agent_a": agent_a, "agent_b": agent_b},
            config=config,
        )

        # Track broadcast creation
        orchestrator.coordination_tracker.add_broadcast_created(
            request_id="test-123",
            sender_id="agent_a",
            question="Test question",
        )

        # Track response
        orchestrator.coordination_tracker.add_broadcast_response(
            request_id="test-123",
            responder_id="agent_b",
            is_human=False,
        )

        # Track completion
        orchestrator.coordination_tracker.add_broadcast_complete(
            request_id="test-123",
            status="complete",
        )

        # Verify events were recorded
        events = orchestrator.coordination_tracker.events
        broadcast_events = [e for e in events if "broadcast" in e.event_type.value]

        assert len(broadcast_events) >= 3  # Created, response, complete


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
