"""
Agent Loop

Core tool execution loop: send messages -> process tool calls -> execute -> repeat.
Stateless function design - state passed in/out explicitly.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable
from typing import TYPE_CHECKING, Any

from .types import (
    AssistantMessage,
    Config,
    DoneEvent,
    ErrorEvent,
    Event,
    ImageEvent,
    ImagePart,
    Message,
    MessageEvent,
    Response,
    SessionUsageEvent,
    TextEvent,
    TextPart,
    ThinkingEvent,
    ThinkingPart,
    Tool,
    ToolCallEvent,
    ToolContext,
    ToolResult,
    ToolResultEvent,
    ToolResultMessage,
    ToolUsePart,
    TurnStartEvent,
    Usage,
    UsageEvent,
    UserMessage,
)

if TYPE_CHECKING:
    from .kits.base import Kit
    from .providers.base import Provider

# Module-level logger for observability
# Apps configure handlers; this enables OTel/Logfire/Weave integration
logger = logging.getLogger("innerloop")


async def execute(
    provider: Provider,
    messages: list[Message],
    tools: list[Tool] | None = None,
    config: Config | None = None,
    tool_choice: dict[str, str] | None = None,
    on_event: Callable[[Event], None] | None = None,
    context: ToolContext | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    kits: list[Kit] | None = None,
    response_tool_name: str | None = None,
) -> tuple[list[Message], Response[Any]]:
    """
    Execute the agent loop.

    Streams from provider, executes tools, repeats until done.

    Args:
        provider: LLM provider to use
        messages: Conversation history (modified in place)
        tools: Available tools (optional)
        config: Execution configuration (optional)
        on_event: Callback for streaming events (optional)
        context: Tool execution context (optional)
        api_key: API key for creating new providers (for skill model override)
        base_url: Base URL for creating new providers (for skill model override)
        kits: List of Kit instances for lifecycle hooks (on_exit, etc.)
        response_tool_name: If provided, force this tool on the final turn
                            (used to ensure structured output before max_turns)

    Returns:
        Tuple of (updated messages, Response object)

    Note: This is a pure function - messages list is copied internally.
    """
    config = config or Config()
    tool_map = {t.name: t for t in (tools or [])}
    all_messages = list(messages)  # Copy to avoid mutating input
    all_tool_results: list[ToolResult] = []
    total_usage = Usage()
    turn = 0
    final_text_parts: list[str] = []
    final_thinking_parts: list[str] = []
    final_images: list[ImagePart] = []
    stop_reason = "end_turn"
    start_time = time.monotonic()
    exit_attempts = 0  # Track on_exit calls to prevent infinite loops
    kits = kits or []

    logger.debug(
        "Starting loop execution",
        extra={
            "llm.model": f"{provider.name}/{provider.model_id}",
            "loop.max_turns": config.max_turns,
            "loop.timeout": config.timeout,
            "tools.count": len(tool_map),
        },
    )

    while turn < config.max_turns:
        # Check timeout
        elapsed = time.monotonic() - start_time
        if elapsed >= config.timeout:
            logger.info(
                "Loop timeout exceeded",
                extra={"loop.elapsed_s": round(elapsed, 2), "loop.turn": turn},
            )
            stop_reason = "timeout"
            break

        turn += 1

        # Emit turn start event
        if on_event:
            on_event(TurnStartEvent(turn=turn))

        # Determine effective tool_choice for this turn
        effective_tool_choice = tool_choice
        # On final turn, force response tool if specified to ensure structured output
        if turn == config.max_turns and response_tool_name:
            effective_tool_choice = {"name": response_tool_name}

        # Stream one turn from provider
        round_result = await _stream_round(
            provider=provider,
            messages=all_messages,
            tools=tools,
            config=config,
            tool_choice=effective_tool_choice,
            on_event=on_event,
        )

        # Clear tool_choice after first turn
        # This allows the model to decide whether to call tools or return text
        # on subsequent turns, preventing infinite loops when tool_choice is forced
        if tool_choice is not None:
            tool_choice = None

        # Unpack round result
        text_parts = round_result["text_parts"]
        thinking_parts = round_result["thinking_parts"]
        images = round_result["images"]
        tool_calls = round_result["tool_calls"]
        usage = round_result["usage"]
        stop_reason = round_result["stop_reason"]
        error = round_result["error"]

        # Aggregate
        final_text_parts.extend(text_parts)
        final_thinking_parts.extend(thinking_parts)
        final_images.extend(images)
        total_usage = total_usage.add(usage)

        # Build assistant message content
        content: list[Any] = []
        # Filter empty thinking parts (some models emit empty thinking blocks)
        thinking_text = "".join(p for p in thinking_parts if p.strip())
        if thinking_text:
            content.append(ThinkingPart(text=thinking_text))
        if text_parts:
            content.append(TextPart(text="".join(text_parts)))
        for img in images:
            content.append(img)
        for tc in tool_calls:
            content.append(ToolUsePart(id=tc["id"], name=tc["name"], input=tc["input"]))

        # Add assistant message
        assistant_msg = AssistantMessage(
            content=content,
            model=f"{provider.name}/{provider.model_id}",
        )
        all_messages.append(assistant_msg)

        # Handle error
        if error:
            error_thinking = "".join(p for p in final_thinking_parts if p.strip())
            return all_messages, Response(
                text="".join(final_text_parts),
                thinking=(error_thinking if error_thinking else None),
                model=f"{provider.name}/{provider.model_id}",
                session_id="",  # Caller sets this
                usage=total_usage,
                tool_results=all_tool_results,
                images=final_images,
                stop_reason="error",
            )

        # Check timeout after turn completes (catches slow single-turn responses)
        elapsed = time.monotonic() - start_time
        if elapsed >= config.timeout:
            stop_reason = "timeout"
            break

        # No tool calls = done (unless kits inject exit messages)
        if not tool_calls:
            # Build kit context for on_exit handlers
            from .kits.base import KitContext

            kit_ctx = KitContext(
                messages=all_messages,
                turn=turn,
                model=f"{provider.name}/{provider.model_id}",
                session_id=context.session_id if context else None,
                workdir=context.workdir if context else None,
                exit_attempts=exit_attempts,
            )

            # Call on_exit for each kit, collect injected messages
            exit_messages: list[Message] = []
            for kit in kits:
                kit_messages = kit.on_exit(kit_ctx)
                if kit_messages:
                    exit_messages.extend(kit_messages)

            # If any exit messages, inject and continue
            if exit_messages:
                exit_attempts += 1
                all_messages.extend(exit_messages)
                continue

            # No exit messages - actually done
            break

        # Execute tools in parallel
        tool_results = await _execute_tools(
            tool_calls=tool_calls,
            tool_map=tool_map,
            on_event=on_event,
            context=context,
        )

        # Add tool result messages and track results
        for tc, (result_content, is_error) in zip(
            tool_calls, tool_results, strict=True
        ):
            tool_msg = ToolResultMessage(
                tool_use_id=tc["id"],
                tool_name=tc["name"],
                content=result_content,
                is_error=is_error,
            )
            all_messages.append(tool_msg)

            # Track for response
            all_tool_results.append(
                ToolResult(
                    tool_use_id=tc["id"],
                    tool_name=tc["name"],
                    input=tc["input"],
                    output=result_content,
                    is_error=is_error,
                )
            )

        # Check for skill activation and inject messages (two-message pattern)
        skill_result = _check_skill_activation(tool_calls, tool_map)
        if skill_result:
            skill_messages, model_override = skill_result
            for msg in skill_messages:
                all_messages.append(msg)

            # Apply model override if specified
            # Note: get_provider resolves api_key from environment if None
            if model_override:
                from .providers import get_provider

                logger.debug(
                    "Skill requested model override",
                    extra={"skill.model_override": model_override},
                )
                provider = get_provider(
                    model=model_override,
                    api_key=api_key,
                    base_url=base_url,
                )

            # Continue to next turn - the LLM will see the skill prompt

    else:
        # Max turns exceeded
        logger.warning(
            "Max turns exceeded",
            extra={"loop.turn": turn, "loop.max_turns": config.max_turns},
        )
        stop_reason = "max_turns"

    elapsed = time.monotonic() - start_time
    logger.debug(
        "Loop execution completed",
        extra={
            "loop.stop_reason": stop_reason,
            "loop.turns": turn,
            "loop.elapsed_s": round(elapsed, 2),
            "llm.tokens.input": total_usage.input_tokens,
            "llm.tokens.output": total_usage.output_tokens,
        },
    )

    # Filter empty thinking parts for final response
    final_thinking = "".join(p for p in final_thinking_parts if p.strip())
    return all_messages, Response(
        text="".join(final_text_parts),
        thinking=(final_thinking if final_thinking else None),
        model=f"{provider.name}/{provider.model_id}",
        session_id="",  # Caller sets this
        usage=total_usage,
        tool_results=all_tool_results,
        images=final_images,
        stop_reason=stop_reason,
    )


async def stream(
    provider: Provider,
    messages: list[Message],
    tools: list[Tool] | None = None,
    config: Config | None = None,
    tool_choice: dict[str, str] | None = None,
    context: ToolContext | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    kits: list[Kit] | None = None,
    response_tool_name: str | None = None,
) -> AsyncIterator[Event]:
    """
    Stream events from the agent loop.

    Yields events as they arrive, including tool results.

    Args:
        provider: LLM provider to use
        messages: Conversation history
        tools: Available tools (optional)
        config: Execution configuration (optional)
        context: Tool execution context (optional)
        kits: List of Kit instances for lifecycle hooks (on_exit, etc.)
        response_tool_name: If provided, force this tool on the final turn
                            (used to ensure structured output before max_turns)

    Yields:
        Event objects
    """
    config = config or Config()
    tool_map = {t.name: t for t in (tools or [])}
    all_messages = list(messages)
    turn = 0
    start_time = time.monotonic()
    total_usage = Usage()
    exit_attempts = 0  # Track on_exit calls to prevent infinite loops
    kits = kits or []

    while turn < config.max_turns:
        # Check timeout
        elapsed = time.monotonic() - start_time
        if elapsed >= config.timeout:
            yield ErrorEvent(error=f"Timeout ({config.timeout}s) exceeded")
            yield SessionUsageEvent(
                input_tokens=total_usage.input_tokens,
                output_tokens=total_usage.output_tokens,
                cache_read_tokens=total_usage.cache_read_tokens,
                cache_write_tokens=total_usage.cache_write_tokens,
                turns=turn,
            )
            yield DoneEvent(stop_reason="timeout")
            return

        turn += 1

        # Emit turn start event
        yield TurnStartEvent(turn=turn)

        tool_calls: list[dict[str, Any]] = []
        text_parts: list[str] = []
        thinking_parts: list[str] = []
        images: list[ImagePart] = []

        # Determine effective tool_choice for this turn
        effective_tool_choice = tool_choice
        # On final turn, force response tool if specified to ensure structured output
        if turn == config.max_turns and response_tool_name:
            effective_tool_choice = {"name": response_tool_name}

        # Stream from provider
        async for event in provider.stream(
            all_messages, tools, config, effective_tool_choice
        ):
            yield event

            if isinstance(event, TextEvent):
                text_parts.append(event.text)
            elif isinstance(event, ThinkingEvent):
                thinking_parts.append(event.text)
            elif isinstance(event, ImageEvent):
                images.append(event.image)
            elif isinstance(event, ToolCallEvent):
                # Clear tool_choice after first turn to avoid forcing same tool
                if tool_choice is not None:
                    tool_choice = None
                tool_calls.append(
                    {
                        "id": event.id,
                        "name": event.name,
                        "input": event.input,
                    }
                )
            elif isinstance(event, UsageEvent):
                total_usage = total_usage.add(event)
            elif isinstance(event, DoneEvent):
                # Check stop reason
                if event.stop_reason != "tool_use":
                    # Check timeout after turn completes (catches slow single-turn)
                    elapsed = time.monotonic() - start_time
                    if elapsed >= config.timeout:
                        yield ErrorEvent(error=f"Timeout ({config.timeout}s) exceeded")
                        yield SessionUsageEvent(
                            input_tokens=total_usage.input_tokens,
                            output_tokens=total_usage.output_tokens,
                            cache_read_tokens=total_usage.cache_read_tokens,
                            cache_write_tokens=total_usage.cache_write_tokens,
                            turns=turn,
                        )
                        yield DoneEvent(stop_reason="timeout")
                        return
                    # Don't return here - let the outer loop check on_exit
                    # The "not tool_calls" block below will handle exit logic

        # Check timeout after turn completes
        elapsed = time.monotonic() - start_time
        if elapsed >= config.timeout:
            yield ErrorEvent(error=f"Timeout ({config.timeout}s) exceeded")
            yield SessionUsageEvent(
                input_tokens=total_usage.input_tokens,
                output_tokens=total_usage.output_tokens,
                cache_read_tokens=total_usage.cache_read_tokens,
                cache_write_tokens=total_usage.cache_write_tokens,
                turns=turn,
            )
            yield DoneEvent(stop_reason="timeout")
            return

        # Build assistant message content (needed for both tool and text responses)
        content: list[Any] = []
        # Filter empty thinking parts (some models emit empty thinking blocks)
        thinking_text = "".join(p for p in thinking_parts if p.strip())
        if thinking_text:
            content.append(ThinkingPart(text=thinking_text))
        if text_parts:
            content.append(TextPart(text="".join(text_parts)))
        for img in images:
            content.append(img)
        for tc in tool_calls:
            content.append(ToolUsePart(id=tc["id"], name=tc["name"], input=tc["input"]))

        # Add assistant message to history (before todo check so context is preserved)
        if content:
            assistant_msg = AssistantMessage(
                content=content,
                model=f"{provider.name}/{provider.model_id}",
            )
            all_messages.append(assistant_msg)

            # Emit complete thinking event for easy log filtering
            # (in addition to streaming chunks already yielded)
            if thinking_text:
                yield ThinkingEvent(text=thinking_text)

            yield MessageEvent(message=assistant_msg)

        # No tool calls = done (unless kits inject exit messages)
        if not tool_calls:
            # Build kit context for on_exit handlers
            from .kits.base import KitContext

            kit_ctx = KitContext(
                messages=all_messages,
                turn=turn,
                model=f"{provider.name}/{provider.model_id}",
                session_id=context.session_id if context else None,
                workdir=context.workdir if context else None,
                exit_attempts=exit_attempts,
            )

            # Call on_exit for each kit, collect injected messages
            exit_messages: list[Message] = []
            for kit in kits:
                kit_messages = kit.on_exit(kit_ctx)
                if kit_messages:
                    exit_messages.extend(kit_messages)

            # If any exit messages, inject and continue
            if exit_messages:
                exit_attempts += 1
                for msg in exit_messages:
                    all_messages.append(msg)
                    yield MessageEvent(message=msg)
                continue

            # No exit messages - actually done
            yield SessionUsageEvent(
                input_tokens=total_usage.input_tokens,
                output_tokens=total_usage.output_tokens,
                cache_read_tokens=total_usage.cache_read_tokens,
                cache_write_tokens=total_usage.cache_write_tokens,
                turns=turn,
            )
            return

        # Execute tools in parallel
        results = await _execute_tools(tool_calls, tool_map, context=context)

        # Add results and yield events
        for tc, (result_content, is_error) in zip(tool_calls, results, strict=True):
            # Add to messages and yield events
            tool_msg = ToolResultMessage(
                tool_use_id=tc["id"],
                tool_name=tc["name"],
                content=result_content,
                is_error=is_error,
            )
            all_messages.append(tool_msg)
            yield MessageEvent(message=tool_msg)

            # Yield result event (for backwards compatibility with event consumers)
            yield ToolResultEvent(
                tool_use_id=tc["id"],
                tool_name=tc["name"],
                content=result_content,
                is_error=is_error,
            )

        # Check for skill activation and inject messages (two-message pattern)
        skill_result = _check_skill_activation(tool_calls, tool_map)
        if skill_result:
            skill_messages, model_override = skill_result
            for msg in skill_messages:
                all_messages.append(msg)
                yield MessageEvent(message=msg)

            # Apply model override if specified
            # Note: get_provider resolves api_key from environment if None
            if model_override:
                from .providers import get_provider

                logger.debug(
                    "Skill requested model override",
                    extra={"skill.model_override": model_override},
                )
                provider = get_provider(
                    model=model_override,
                    api_key=api_key,
                    base_url=base_url,
                )

            # Continue to next turn - the LLM will see the skill prompt

    # Max turns exceeded
    yield ErrorEvent(error=f"Max turns ({config.max_turns}) exceeded")
    yield SessionUsageEvent(
        input_tokens=total_usage.input_tokens,
        output_tokens=total_usage.output_tokens,
        cache_read_tokens=total_usage.cache_read_tokens,
        cache_write_tokens=total_usage.cache_write_tokens,
        turns=turn,
    )
    yield DoneEvent(stop_reason="max_turns")


async def _stream_round(
    provider: Provider,
    messages: list[Message],
    tools: list[Tool] | None,
    config: Config,
    tool_choice: dict[str, str] | None,
    on_event: Callable[[Event], None] | None,
) -> dict[str, Any]:
    """Stream one round from the provider and collect results."""
    text_parts: list[str] = []
    thinking_parts: list[str] = []
    images: list[ImagePart] = []
    tool_calls: list[dict[str, Any]] = []
    usage = Usage()
    stop_reason = "end_turn"
    error: str | None = None

    async for event in provider.stream(
        messages, tools, config, tool_choice=tool_choice
    ):
        if on_event:
            on_event(event)

        if isinstance(event, TextEvent):
            text_parts.append(event.text)
        elif isinstance(event, ThinkingEvent):
            thinking_parts.append(event.text)
        elif isinstance(event, ImageEvent):
            images.append(event.image)
        elif isinstance(event, ToolCallEvent):
            tool_calls.append(
                {
                    "id": event.id,
                    "name": event.name,
                    "input": event.input,
                }
            )
        elif isinstance(event, UsageEvent):
            usage = usage.add(event)
        elif isinstance(event, ErrorEvent):
            error = event.error
        elif isinstance(event, DoneEvent):
            stop_reason = event.stop_reason

    return {
        "text_parts": text_parts,
        "thinking_parts": thinking_parts,
        "images": images,
        "tool_calls": tool_calls,
        "usage": usage,
        "stop_reason": stop_reason,
        "error": error,
    }


async def _execute_tools(
    tool_calls: list[dict[str, Any]],
    tool_map: dict[str, Tool],
    on_event: Callable[[Event], None] | None = None,
    context: ToolContext | None = None,
) -> list[tuple[str, bool]]:
    """Execute tools in parallel.

    Args:
        tool_calls: List of tool calls from LLM
        tool_map: Map of tool name to Tool instance
        on_event: Optional callback for events
        context: Optional tool execution context

    Returns:
        List of (result_content, is_error) tuples
    """

    async def run_one(tc: dict[str, Any]) -> tuple[str, bool]:
        tool = tool_map.get(tc["name"])
        if tool is None:
            logger.warning(
                "Unknown tool requested",
                extra={"tool.name": tc["name"], "tool.id": tc["id"]},
            )
            return f"Unknown tool: {tc['name']}", True

        tool_input = tc["input"]

        start_time = time.monotonic()
        logger.debug(
            "Executing tool",
            extra={"tool.name": tc["name"], "tool.id": tc["id"]},
        )

        timeout_s = context.tool_timeout if context else None
        try:
            result, is_error = await asyncio.wait_for(
                tool.execute(tool_input, context), timeout=timeout_s
            )
        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.warning(
                "Tool execution timed out",
                extra={
                    "tool.name": tc["name"],
                    "tool.duration_ms": duration_ms,
                    "tool.timeout_s": timeout_s,
                    "error.occurred": True,
                },
            )
            result, is_error = (
                f"Tool {tc['name']} timed out after {timeout_s} seconds",
                True,
            )

        duration_ms = int((time.monotonic() - start_time) * 1000)
        if is_error:
            logger.warning(
                "Tool execution failed",
                extra={
                    "tool.name": tc["name"],
                    "tool.duration_ms": duration_ms,
                    "error.occurred": True,
                },
            )
        else:
            logger.debug(
                "Tool execution completed",
                extra={"tool.name": tc["name"], "tool.duration_ms": duration_ms},
            )

        # Emit result event if callback provided
        if on_event:
            on_event(
                ToolResultEvent(
                    tool_use_id=tc["id"],
                    tool_name=tc["name"],
                    content=result,
                    is_error=is_error,
                )
            )

        return result, is_error

    # Execute all tools in parallel
    results = await asyncio.gather(*[run_one(tc) for tc in tool_calls])
    return list(results)


def _check_skill_activation(
    tool_calls: list[dict[str, Any]],
    tool_map: dict[str, Tool],
) -> tuple[list[UserMessage], str | None] | None:
    """Check if a Skill tool was called and return its activation messages.

    Args:
        tool_calls: List of tool calls that were executed
        tool_map: Map of tool name to Tool instance

    Returns:
        Tuple of (messages, model_override) if skill activated, None otherwise.
        model_override is the model to switch to, or None if no override.
    """
    # Import here to avoid circular imports
    from .tooling.skill_tools import SkillTool

    for tc in tool_calls:
        tool = tool_map.get(tc["name"])
        if isinstance(tool, SkillTool):
            activation = tool.get_activation()
            if activation is not None:
                # Convert SkillMessages to UserMessages
                messages = []
                for sm in activation.messages:
                    messages.append(UserMessage(content=sm.content, is_meta=sm.is_meta))
                # Extract model override from context modification
                model_override = activation.context_modification.model_override
                return (messages, model_override)
    return None


__all__ = ["execute", "stream"]
