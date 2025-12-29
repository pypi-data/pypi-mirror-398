#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Send Message Data Models.

This module re-exports standard types from ag_ui_protocol for HTTP communication.
All types conform to ag_ui_protocol standards for interoperability.
"""

from ag_ui.core import (
    # Input types
    RunAgentInput,
    Message,
    Tool,
    Context,
    # Event types
    Event,
    TextMessageContentEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    RunErrorEvent,
    RunStartedEvent,
    RunFinishedEvent,
    # Supporting types
    ToolCall,
    FunctionCall,
    # Message types
    SystemMessage,
    UserMessage,
    ToolMessage,
    AssistantMessage,
)

# Legacy compatibility types (will be removed in future versions)
from typing import Union

ClientMessage = Union[SystemMessage, UserMessage, ToolMessage, AssistantMessage]

# Re-export for convenience
__all__ = [
    "RunAgentInput",
    "Message",
    "Tool",
    "Context",
    "Event",
    "TextMessageContentEvent",
    "ToolCallStartEvent",
    "ToolCallArgsEvent",
    "ToolCallEndEvent",
    "ToolCallResultEvent",
    "RunErrorEvent",
    "RunStartedEvent",
    "RunFinishedEvent",
    "ToolCall",
    "FunctionCall",
    "SystemMessage",
    "UserMessage",
    "ToolMessage",
    "AssistantMessage",
    "ClientMessage",
]
