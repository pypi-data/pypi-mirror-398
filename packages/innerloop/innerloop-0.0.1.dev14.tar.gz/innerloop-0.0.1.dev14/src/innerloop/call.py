"""
One-Shot Call API

Single LLM calls without agent looping.
For structured extraction, tool routing, classification, and simple completions.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Coroutine
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, cast, overload

from .providers import get_provider
from .schema import validate as schema_validate
from .structured import ResponseTool
from .types import (
    Config,
    DoneEvent,
    Message,
    TextEvent,
    ThinkingEvent,
    Tool,
    ToolCallEvent,
    ToolResult,
    Usage,
    UsageEvent,
    UserMessage,
)

T = TypeVar("T")


def _run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run a coroutine synchronously, handling nested event loops.

    If called from within an existing event loop (e.g., Jupyter notebook,
    async web framework), runs the coroutine in a thread pool executor
    with its own event loop. Otherwise, uses asyncio.run() directly.
    """
    try:
        asyncio.get_running_loop()
        # Inside an event loop - run in a thread with its own loop
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No running loop - use asyncio.run directly
        return asyncio.run(coro)


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class ToolCall:
    """Tool call requested by the model.

    Attributes:
        id: Unique identifier for this tool call (from the API)
        name: Name of the tool to call
        arguments: Parsed arguments dict
        fn: Reference to the Tool object (for invoke)

    Example:
        result = call(..., tools=[get_weather], invoke_tools=False)
        for tc in result.tool_calls:
            # Inspect first
            if tc.arguments.get("city") in allowed_cities:
                # Then invoke
                output = tc.invoke()  # or tc()
    """

    id: str
    name: str
    arguments: dict[str, Any]
    fn: Tool | None = None  # Reference to the tool for invoke()

    async def ainvoke(self) -> ToolResult:
        """Execute this tool call asynchronously.

        Returns:
            ToolResult with output and error status
        """
        if self.fn is None:
            return ToolResult(
                tool_use_id=self.id,
                tool_name=self.name,
                input=self.arguments,
                output=f"Unknown tool: {self.name}",
                is_error=True,
            )

        result_content, is_error = await self.fn.execute(self.arguments, None)
        return ToolResult(
            tool_use_id=self.id,
            tool_name=self.name,
            input=self.arguments,
            output=result_content,
            is_error=is_error,
        )

    def invoke(self) -> ToolResult:
        """Execute this tool call synchronously.

        Returns:
            ToolResult with output and error status
        """
        return _run_sync(self.ainvoke())

    def __call__(self) -> ToolResult:
        """Shorthand for invoke()."""
        return self.invoke()


# Generic type variable for CallResponse output
OutputT = TypeVar("OutputT")


@dataclass
class CallResponse(Generic[OutputT]):
    """Result of a one-shot call().

    Attributes:
        text: Model's text response
        output: Structured output (if response_format used), otherwise same as text
        tool_calls: Tool calls requested by model
        tool_results: Results of tool execution (if invoke_tools=True)
        usage: Token usage
        stop_reason: Why generation stopped ("end_turn", "tool_use", etc.)

    Type Parameters:
        OutputT: The type of the structured output. Defaults to str when no
                 response_format is provided.
    """

    text: str
    output: OutputT | str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    stop_reason: str = "end_turn"

    def __post_init__(self) -> None:
        """Set output to text if not explicitly set."""
        if self.output == "":
            self.output = self.text


# =============================================================================
# Core Implementation
# =============================================================================


async def _execute_tool(
    tool: Tool,
    tool_call: ToolCall,
) -> ToolResult:
    """Execute a single tool and return result."""
    result_content, is_error = await tool.execute(tool_call.arguments, None)
    return ToolResult(
        tool_use_id=tool_call.id,
        tool_name=tool_call.name,
        input=tool_call.arguments,
        output=result_content,
        is_error=is_error,
    )


@overload
async def acall(
    prompt: str,
    model: str,
    *,
    tools: list[Tool] | None = None,
    response_format: None = None,
    invoke_tools: bool = True,
    system: str | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float = 300.0,
) -> CallResponse[str]: ...


@overload
async def acall(
    prompt: str,
    model: str,
    *,
    tools: list[Tool] | None = None,
    response_format: type[T],
    invoke_tools: bool = True,
    system: str | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float = 300.0,
) -> CallResponse[T]: ...


async def acall(
    prompt: str,
    model: str,
    *,
    tools: list[Tool] | None = None,
    response_format: type[T] | None = None,
    invoke_tools: bool = True,
    system: str | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float = 300.0,
) -> CallResponse[T] | CallResponse[str]:
    """
    Make a single LLM call without looping.

    Args:
        prompt: User prompt
        model: Model string (e.g., "openrouter/anthropic/claude-sonnet-4")
        tools: Available tools for the model to call
        response_format: Pydantic model for structured output
        invoke_tools: Whether to execute tool calls (default: True)
        system: System prompt
        max_output_tokens: Max tokens in response
        temperature: Sampling temperature
        timeout: Request timeout in seconds

    Returns:
        CallResponse with text, tool_calls, tool_results, and usage
    """
    # Get provider
    provider = get_provider(model=model)

    # Build message (explicit Message type for list variance)
    messages: list[Message] = [UserMessage(content=prompt)]

    # Build config
    config_kwargs: dict[str, Any] = {"system": system, "timeout": timeout}
    if max_output_tokens is not None:
        config_kwargs["max_output_tokens"] = max_output_tokens
    if temperature is not None:
        config_kwargs["temperature"] = temperature
    config = Config(**config_kwargs)

    # Handle structured output via response_format
    actual_tools = list(tools) if tools else []
    respond_tool: ResponseTool | None = None
    if response_format is not None:
        respond_tool = ResponseTool(response_format)
        actual_tools.append(respond_tool)

    # Stream from provider (single call)
    text_parts: list[str] = []
    thinking_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    usage = Usage()
    stop_reason = "end_turn"

    async for event in provider.stream(
        messages, actual_tools if actual_tools else None, config
    ):
        if isinstance(event, TextEvent):
            text_parts.append(event.text)
        elif isinstance(event, ThinkingEvent):
            thinking_parts.append(event.text)
        elif isinstance(event, ToolCallEvent):
            tool_calls.append(
                ToolCall(
                    id=event.id,
                    name=event.name,
                    arguments=event.input,
                )
            )
        elif isinstance(event, UsageEvent):
            usage = usage.add(event)
        elif isinstance(event, DoneEvent):
            stop_reason = event.stop_reason

    # Build tool map and attach fn references to tool calls
    tool_map = {t.name: t for t in actual_tools}
    for tc in tool_calls:
        tc.fn = tool_map.get(tc.name)

    # Execute tools if requested
    tool_results: list[ToolResult] = []
    validated_output: Any = None

    if invoke_tools and tool_calls:
        # Execute all tools in parallel
        tasks = []
        for tc in tool_calls:
            tool = tool_map.get(tc.name)
            if tool is not None:
                tasks.append(_execute_tool(tool, tc))

        if tasks:
            results = await asyncio.gather(*tasks)
            tool_results = list(results)

            # Check for structured output from respond tool
            if respond_tool is not None:
                for tr in tool_results:
                    if tr.tool_name == "respond" and not tr.is_error:
                        try:
                            validated_output = schema_validate(
                                response_format, tr.input
                            )
                        except Exception:
                            pass  # Validation failed, output stays None

    # If response_format but no validated output yet, try to validate from tool call
    if response_format is not None and validated_output is None:
        for tc in tool_calls:
            if tc.name == "respond":
                try:
                    validated_output = schema_validate(response_format, tc.arguments)
                except Exception:
                    pass

    return CallResponse(
        text="".join(text_parts),
        output=validated_output
        if validated_output is not None
        else "".join(text_parts),
        tool_calls=tool_calls,
        tool_results=tool_results,
        usage=usage,
        stop_reason=stop_reason,
    )


@overload
def call(
    prompt: str,
    model: str,
    *,
    tools: list[Tool] | None = None,
    response_format: None = None,
    invoke_tools: bool = True,
    system: str | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float = 300.0,
) -> CallResponse[str]: ...


@overload
def call(
    prompt: str,
    model: str,
    *,
    tools: list[Tool] | None = None,
    response_format: type[T],
    invoke_tools: bool = True,
    system: str | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float = 300.0,
) -> CallResponse[T]: ...


def call(
    prompt: str,
    model: str,
    *,
    tools: list[Tool] | None = None,
    response_format: type[T] | None = None,
    invoke_tools: bool = True,
    system: str | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float = 300.0,
) -> CallResponse[T] | CallResponse[str]:
    """
    Make a single LLM call without looping (sync version).

    Args:
        prompt: User prompt
        model: Model string (e.g., "openrouter/anthropic/claude-sonnet-4")
        tools: Available tools for the model to call
        response_format: Pydantic model for structured output
        invoke_tools: Whether to execute tool calls (default: True)
        system: System prompt
        max_output_tokens: Max tokens in response
        temperature: Sampling temperature
        timeout: Request timeout in seconds

    Returns:
        CallResponse with text, tool_calls, tool_results, and usage
    """
    result = _run_sync(
        acall(
            prompt=prompt,
            model=model,
            tools=tools,
            response_format=response_format,
            invoke_tools=invoke_tools,
            system=system,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            timeout=timeout,
        )
    )
    return cast("CallResponse[T] | CallResponse[str]", result)


__all__ = ["call", "acall", "CallResponse", "ToolCall"]
