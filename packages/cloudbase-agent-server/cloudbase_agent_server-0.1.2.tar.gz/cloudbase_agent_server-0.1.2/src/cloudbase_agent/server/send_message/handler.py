#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTTP Request Handler for Send Message.

This module provides HTTP protocol-level mapping and request handling
for the Cloudbase Agent send_message endpoint. It processes incoming requests,
converts between client and internal message formats, and manages agent
execution with real-time event streaming support.
"""

import logging
from typing import Any, AsyncGenerator

from ag_ui.core.events import EventType

from .models import (
    Event,
    TextMessageContentEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    RunErrorEvent,
    RunAgentInput,
)

logger = logging.getLogger(__name__)


async def handler(input_data: RunAgentInput, agent: Any) -> AsyncGenerator[Event, None]:
    """Handle HTTP requests and process agent execution with streaming.

    This function serves as the main request handler for the send_message endpoint.
    It processes agent events and streams back properly formatted events conforming
    to ag_ui_protocol standards.

    Args:
        input_data: Standard run agent input containing messages and config
        agent: The agent instance to execute (must have a 'run' method)

    Yields:
        Standard protocol events (TEXT_MESSAGE_CONTENT, TOOL_CALL_*, etc.)

    Raises:
        RuntimeError: When agent execution or message processing fails
    """
    try:
        logger.info("Agent run started: run_id=%s thread_id=%s", input_data.run_id, input_data.thread_id)
        
        event_count = 0

        async for event in agent.run(input_data):
            event_count += 1
            
            # Handle different event types with raw_event tracking for delta extraction
            if event.type == EventType.TEXT_MESSAGE_CONTENT:
                # Extract delta from framework-specific raw event structure
                # Priority: raw_event (for framework compatibility) -> event.delta (standard fallback)
                content = None
                
                if event.raw_event:
                    raw_data = event.raw_event.get("data", {})
                    chunk = raw_data.get("chunk", {})
                    content = chunk.get("content")
                
                # Fallback to event.delta if raw_event extraction failed
                if content is None:
                    content = getattr(event, "delta", None)

                if content:
                    yield TextMessageContentEvent(
                        message_id=event.message_id,
                        delta=content,
                    )

            elif event.type == EventType.TEXT_MESSAGE_CHUNK:
                # Handle text chunk events with fallback to event.delta
                # Priority: raw_event (for framework compatibility) -> event.delta (standard fallback)
                content = None
                
                if event.raw_event:
                    raw_data = event.raw_event.get("data", {})
                    chunk = raw_data.get("chunk", {})
                    content = chunk.get("content")
                
                # Fallback to event.delta if raw_event extraction failed
                if content is None:
                    content = getattr(event, "delta", None)

                if content:
                    yield TextMessageContentEvent(
                        message_id=event.message_id,
                        delta=content,
                    )

            elif event.type == EventType.TOOL_CALL_START:
                # Emit tool call start event
                yield ToolCallStartEvent(
                    tool_call_id=event.tool_call_id,
                    tool_call_name=event.tool_call_name,  # ✓ Correct field name
                )

                # Some frameworks provide initial args in start event
                start_delta = None
                if event.raw_event is not None:
                    start_delta = (
                        event.raw_event.get("data", {})
                        .get("chunk", {})
                        .get("tool_call_chunks", [{}])[0]
                        .get("args")
                    )

                if start_delta is not None:
                    yield ToolCallArgsEvent(
                        tool_call_id=event.tool_call_id,
                        delta=start_delta,
                    )

            elif event.type in (EventType.TOOL_CALL_ARGS, EventType.TOOL_CALL_CHUNK):
                # Handle streaming tool arguments
                yield ToolCallArgsEvent(
                    tool_call_id=event.tool_call_id,
                    delta=event.delta,
                )

            elif event.type == EventType.TOOL_CALL_END:
                # Tool call arguments complete
                yield ToolCallEndEvent(
                    tool_call_id=event.tool_call_id,
                )

            elif event.type == EventType.TOOL_CALL_RESULT:
                # Tool execution result
                yield ToolCallResultEvent(
                    tool_call_id=event.tool_call_id,
                    result=event.content,
                )

            # Note: CUSTOM events for interrupts are handled by ag_ui_protocol internally

        logger.info("Agent run completed: run_id=%s total_events=%d", input_data.run_id, event_count)

    except Exception as e:
        logger.error("Agent run failed: run_id=%s error=%s", input_data.run_id, str(e))
        yield RunErrorEvent(run_id=input_data.run_id, message=str(e))
        raise RuntimeError(f"Failed to process agent request: {str(e)}") from e
