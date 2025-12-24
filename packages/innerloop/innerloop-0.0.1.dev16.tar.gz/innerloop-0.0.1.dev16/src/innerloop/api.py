"""
Loop API

Public interface for InnerLoop.
Provides sync and async methods for running agent loops.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import shutil
import tempfile
from collections.abc import AsyncIterator, Coroutine, Generator, Iterator
from pathlib import Path
from queue import Queue
from threading import Thread
from typing import Any, TypeVar, cast, overload

from .kits.base import Kit
from .loop import execute as loop_execute
from .loop import stream as loop_stream
from .providers import get_provider
from .schema import validate as schema_validate
from .session import SessionStore
from .structured import ResponseTool
from .tooling.skill_tools import create_skill_tools
from .tooling.skills import SkillState, list_skills
from .types import (
    Config,
    DoneEvent,
    Event,
    ImagePart,
    Message,
    MessageEvent,
    Response,
    StructuredOutputEvent,
    TextEvent,
    TextPart,
    ThinkingConfig,
    ThinkingEvent,
    ThinkingLevel,
    Tool,
    ToolCallEvent,
    ToolContext,
    ToolResultEvent,
    UsageEvent,
    UserMessage,
)

T = TypeVar("T")


# =============================================================================
# Image Helpers
# =============================================================================


def _guess_media_type(path: Path) -> str:
    """Infer MIME type from file extension."""
    ext = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def _resolve_image(img: str | Path) -> ImagePart:
    """Convert URL or file path to ImagePart.

    Args:
        img: HTTP(S) URL or local file path

    Returns:
        ImagePart with either url or base64_data set
    """
    import base64

    if isinstance(img, str) and img.startswith(("http://", "https://")):
        return ImagePart(url=img)
    else:
        path = Path(img)
        data = base64.b64encode(path.read_bytes()).decode()
        media_type = _guess_media_type(path)
        return ImagePart(base64_data=data, media_type=media_type)


def _build_user_content(
    prompt: str | None, images: list[str | Path] | None
) -> str | list[TextPart | ImagePart]:
    """Build user message content from prompt and images.

    Args:
        prompt: Text prompt (optional if images provided)
        images: List of image URLs or file paths (optional)

    Returns:
        Either a string (text-only) or list of content parts (multimodal)
    """
    if not images:
        return prompt or ""

    # Build multimodal content
    content: list[TextPart | ImagePart] = []
    if prompt:
        content.append(TextPart(text=prompt))
    for img in images:
        content.append(_resolve_image(img))
    return content


# =============================================================================
# Sync Helpers
# =============================================================================


def _run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run a coroutine synchronously, handling nested event loops.

    If called from within an existing event loop (e.g., Jupyter notebook,
    async web framework), runs the coroutine in a thread pool executor
    with its own event loop. Otherwise, uses asyncio.run() directly.

    Args:
        coro: The coroutine to execute

    Returns:
        The result of the coroutine
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


class Loop:
    """
    Agent loop with session management.

    Examples:
        # Simple usage
        loop = Loop(model="anthropic/claude-sonnet-4")
        response = loop.run("Hello!")

        # With tools
        @tool
        def get_weather(city: str) -> str:
            return f"Weather in {city}: 72°F"

        loop = Loop(
            model="anthropic/claude-sonnet-4",
            tools=[get_weather],
        )
        response = loop.run("What's the weather in NYC?")

        # Streaming
        for event in loop.stream("Tell me a story"):
            if isinstance(event, TextEvent):
                print(event.text, end="", flush=True)
    """

    def __init__(
        self,
        model: str,
        tools: list[Tool] | None = None,
        kits: list[Kit] | None = None,
        thinking: ThinkingLevel | ThinkingConfig | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        system: str | None = None,
        workdir: Path | str | None = None,
        load_agents_md: bool = True,
        session: str | None = None,
        tool_timeout: float | None = None,
        timeout: float = 300.0,
        response_modalities: list[str] | None = None,
        # Skills configuration
        skills_paths: list[Path | str] | None = None,
        skills_preload: bool = True,
        skills_token_budget: int = 15000,
        # File access control
        read_paths: list[Path | str] | None = None,
        write_paths: list[Path | str] | None = None,
    ):
        """
        Initialize a Loop.

        Args:
            model: Model string (e.g., "anthropic/claude-sonnet-4").
            tools: List of tools (functions decorated with @tool).
                   Default: [] (no tools).
            kits: List of Kit instances. Kits bundle tools with shared state
                  and lifecycle hooks (on_exit, on_tool_error, etc.).
                  Kit tools are added to the tool list automatically.
            thinking: Thinking level or config (optional).
            api_key: Explicit API key (optional, uses env var otherwise).
            base_url: Custom base URL (optional, for local models).
            system: System prompt (optional).
            workdir: Working directory for tools (default: current directory).
            load_agents_md: If True and workdir is set, auto-load AGENTS.md from
                           workdir and prepend to system prompt. Default: True.
            session: Session ID to resume (from a previous response.session_id).
                     If None, creates a new session with auto-generated ID.
            tool_timeout: Timeout in seconds for tool execution.
                         Default: None (auto-computed as 80% of timeout).
            timeout: Total loop execution timeout in seconds (default: 300.0).
            response_modalities: Output modalities for image generation models.
                                Use ["TEXT", "IMAGE"] to enable image generation.
                                Default: None (provider decides).
            skills_paths: List of directories to search for skills.
                         Skills are discovered in subdirectories containing SKILL.md.
                         Later paths override earlier ones (same skill name).
                         Default: None (no skills).
            skills_preload: Add skill metadata to Skill tool description.
                           When True, skills are loaded at startup and their
                           names/descriptions appear in the Skill tool.
                           Default: True.
            skills_token_budget: Max characters for available_skills section
                                in Skill tool description. Default: 15000.
            read_paths: List of paths with read-only access. File tools can read,
                       glob, and grep these paths but not write to them.
                       Supports Path objects, strings, and ~ expansion.
                       Default: None (only workdir is readable).
            write_paths: List of paths with read+write access. Write implies read.
                        File tools can read and write to these paths.
                        Default: None (only workdir is writable).
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

        # Compute tool_timeout: default to 80% of loop timeout, cap at 80%
        if tool_timeout is None:
            self.tool_timeout = timeout * 0.8
        else:
            # Cap tool_timeout at 80% of loop timeout
            self.tool_timeout = min(tool_timeout, timeout * 0.8)

        # Set up working directory
        self.workdir = Path(workdir).resolve() if workdir else Path.cwd()

        # Set up file access paths
        self.read_paths: tuple[Path, ...] = tuple(
            Path(p).expanduser().resolve() for p in (read_paths or [])
        )
        self.write_paths: tuple[Path, ...] = tuple(
            Path(p).expanduser().resolve() for p in (write_paths or [])
        )

        # Load AGENTS.md if enabled and workdir was explicitly set
        agents_md_content = None
        if load_agents_md and workdir is not None:
            agents_md_content = self._load_agents_md()

        # Build final system prompt (AGENTS.md + explicit system)
        self.system: str | None
        if agents_md_content and system:
            self.system = agents_md_content + "\n\n" + system
        elif agents_md_content:
            self.system = agents_md_content
        else:
            self.system = system

        # Kits (store for lifecycle handlers)
        self.kits: list[Kit] = list(kits) if kits else []

        # Tools (default to empty list, then add kit tools)
        self.tools: list[Tool] = list(tools) if tools else []
        for kit in self.kits:
            self.tools.extend(kit.get_tools())

        # Configure thinking
        if isinstance(thinking, ThinkingLevel):
            self.thinking: ThinkingConfig | None = ThinkingConfig(level=thinking)
        else:
            self.thinking = thinking

        # Configure response modalities (for image generation models)
        self.response_modalities = response_modalities

        # Session management
        self._store = SessionStore()
        if session:
            self.session_id = session
            self.messages = self._store.load(session)
            # Rehydrate kit state from session history
            for kit in self.kits:
                kit.rehydrate(self.messages)
        else:
            self.session_id = self._store.new_session_id()
            self.messages = []

        # Skills system: load skills and create skill tools
        self.skill_state: SkillState | None = None
        if skills_paths:
            # Convert paths to Path objects
            paths = [Path(p).expanduser() for p in skills_paths]

            # Load skills if preload is enabled
            if skills_preload:
                skills = list_skills(paths)
            else:
                skills = []

            # Create skill state
            self.skill_state = SkillState(
                skills=skills,
                skills_paths=paths,
            )

            # Create and add skill tools
            skill_tools = create_skill_tools(self.skill_state, skills_token_budget)
            self.tools.extend(skill_tools)

        # Get provider
        self._provider = get_provider(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
        )

        # Temp directory for overflow files (lazily created)
        self._temp_dir: Path | None = None

    def _load_agents_md(self) -> str | None:
        """Load AGENTS.md from workdir if it exists.

        Checks AGENTS.md (uppercase) first, then agents.md (lowercase).
        Returns None if neither exists or if file is unreadable.
        """
        # Check uppercase first (preferred)
        agents_path = self.workdir / "AGENTS.md"
        if not agents_path.exists():
            # Try lowercase fallback
            agents_path = self.workdir / "agents.md"

        if not agents_path.exists():
            return None

        try:
            content = agents_path.read_text(encoding="utf-8")
            # Size limit: 100KB
            if len(content) > 100_000:
                import warnings

                warnings.warn(
                    f"AGENTS.md exceeds 100KB limit ({len(content)} bytes), truncating",
                    stacklevel=2,
                )
                content = content[:100_000]
            return content
        except Exception:
            # Log warning but don't fail
            import warnings

            warnings.warn(
                f"Could not read {agents_path}, proceeding without it", stacklevel=2
            )
            return None

    @property
    def temp_dir(self) -> Path:
        """Lazily create temp directory for overflow files (e.g., bash output)."""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="innerloop-"))
        return self._temp_dir

    def cleanup(self) -> None:
        """Clean up temp directory. Call when done with the Loop."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None

    def __enter__(self) -> Loop:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit - cleanup temp directory."""
        self.cleanup()

    def _build_config(self, **overrides: Any) -> Config:
        """Build config with thinking, system prompt, and response modalities."""
        config = Config(
            system=self.system,
            thinking=self.thinking,
            response_modalities=self.response_modalities,
            **overrides,
        )
        return config

    def _make_config(
        self,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
    ) -> Config:
        """Build config from optional parameters, filtering None values."""
        kwargs: dict[str, Any] = {}
        if max_output_tokens is not None:
            kwargs["max_output_tokens"] = max_output_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature
        if timeout is not None:
            kwargs["timeout"] = timeout
        if max_turns is not None:
            kwargs["max_turns"] = max_turns
        return self._build_config(**kwargs)

    def _save_message(self, message: Message) -> None:
        """Save a message to the session."""
        self._store.append(
            self.session_id, message, model=self.model, workdir=self.workdir
        )

    @overload
    async def arun(
        self,
        prompt: str | None = None,
        response_format: None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> Response[str]: ...

    @overload
    async def arun(
        self,
        prompt: str | None = None,
        response_format: type[T] = ...,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> Response[T]: ...

    async def arun(
        self,
        prompt: str | None = None,
        response_format: type[T] | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> Response[T] | Response[str]:
        """
        Run a prompt asynchronously.

        Args:
            prompt: User prompt (optional if images provided).
            response_format: Pydantic model class for structured output (optional).
                            When provided, forces the model to call a 'respond' tool
                            and validates the output against this schema.
            max_output_tokens: Maximum tokens in response (default: 8192).
            temperature: Sampling temperature (optional).
            timeout: Total loop timeout in seconds (default: 300.0).
            max_turns: Maximum agent loop iterations (default: 50).
            validation_retries: Max validation retry attempts for structured output.
            images: List of image URLs or file paths for vision models (optional).

        Returns:
            Response object. If response_format is provided, response.output
            contains the validated Pydantic model instance.
        """
        # Handle structured output via response_format
        if response_format is not None:
            return await self._arun_structured(
                prompt=prompt,
                output_type=response_format,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                timeout=timeout,
                max_turns=max_turns,
                validation_retries=validation_retries,
                images=images,
            )

        # Build user message content (handles images if provided)
        content = _build_user_content(prompt, images)
        user_msg = UserMessage(content=content)
        self.messages.append(user_msg)
        self._save_message(user_msg)

        # Build config
        config = self._make_config(max_output_tokens, temperature, timeout, max_turns)

        # Create tool context
        tool_context = ToolContext(
            workdir=self.workdir,
            session_id=self.session_id,
            model=self.model,
            tool_timeout=self.tool_timeout,
            temp_dir=self.temp_dir,  # Lazily created when first accessed
            read_paths=self.read_paths,
            write_paths=self.write_paths,
        )

        # Execute agent loop
        updated_messages, response = await loop_execute(
            provider=self._provider,
            messages=self.messages,
            tools=self.tools,
            config=config,
            context=tool_context,
            api_key=self.api_key,
            base_url=self.base_url,
            kits=self.kits,
        )

        # Update messages and save new ones
        new_messages = updated_messages[len(self.messages) :]
        for msg in new_messages:
            self._save_message(msg)
        self.messages = updated_messages

        # Set session ID on response
        response.session_id = self.session_id

        return response

    async def _arun_structured(
        self,
        prompt: str | None,
        output_type: type[T],
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> Response[T]:
        """
        Internal method for structured output execution.

        Creates a ResponseTool, injects it into the tools list, and streams
        events until respond is called successfully (with early exit).
        """
        from .types import ToolResult, Usage

        # Collect events from streaming and return as Response
        # This allows early exit when respond succeeds
        text_parts: list[str] = []
        thinking_parts: list[str] = []
        tool_results: list[ToolResult] = []
        usage: Usage | None = None
        stop_reason = "end_turn"
        validated_output: T | None = None

        # Track tool calls to get the input (since ToolResultEvent only has output)
        pending_tool_calls: dict[
            str, tuple[str, dict[str, Any]]
        ] = {}  # id -> (name, input)

        async for event in self._astream_structured(
            prompt=prompt,
            output_type=output_type,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            timeout=timeout,
            max_turns=max_turns,
            validation_retries=validation_retries,
            images=images,
        ):
            # Collect relevant data from events
            if isinstance(event, TextEvent):
                text_parts.append(event.text)
            elif isinstance(event, ThinkingEvent):
                thinking_parts.append(event.text)
            elif isinstance(event, ToolCallEvent):
                # Track tool call for later result matching
                pending_tool_calls[event.id] = (event.name, event.input)
            elif isinstance(event, ToolResultEvent):
                # Get input from tracked tool call
                tool_name, tool_input = pending_tool_calls.get(
                    event.tool_use_id, (event.tool_name, {})
                )
                tool_results.append(
                    ToolResult(
                        tool_use_id=event.tool_use_id,
                        tool_name=event.tool_name,
                        input=tool_input,
                        output=event.content,
                        is_error=event.is_error,
                    )
                )
            elif isinstance(event, UsageEvent):
                if usage is None:
                    usage = Usage(
                        input_tokens=event.input_tokens,
                        output_tokens=event.output_tokens,
                    )
                else:
                    # Accumulate usage
                    usage = usage.add(
                        Usage(
                            input_tokens=event.input_tokens,
                            output_tokens=event.output_tokens,
                        )
                    )
            elif isinstance(event, DoneEvent):
                stop_reason = event.stop_reason
            elif isinstance(event, StructuredOutputEvent):
                validated_output = event.output

        # Build response
        # Note: validated_output can be None if validation failed, but the Response
        # class handles this via its default (falls back to text). The cast tells
        # the type checker we're intentionally passing T | None.
        response = cast(
            "Response[T]",
            Response(
                text="".join(text_parts),
                thinking="".join(thinking_parts) if thinking_parts else None,
                model=f"{self._provider.name}/{self._provider.model_id}",
                session_id=self.session_id,
                usage=usage or Usage(input_tokens=0, output_tokens=0),
                tool_results=tool_results,
                stop_reason=stop_reason,
                output=validated_output,
            ),
        )

        return response

    @overload
    def run(
        self,
        prompt: str | None = None,
        response_format: None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> Response[str]: ...

    @overload
    def run(
        self,
        prompt: str | None = None,
        response_format: type[T] = ...,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> Response[T]: ...

    def run(
        self,
        prompt: str | None = None,
        response_format: type[T] | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> Response[T] | Response[str]:
        """
        Run a prompt synchronously.

        Args:
            prompt: User prompt (optional if images provided).
            response_format: Pydantic model class for structured output (optional).
                            When provided, forces the model to call a 'respond' tool
                            and validates the output against this schema.
            max_output_tokens: Maximum tokens in response (default: 8192).
            temperature: Sampling temperature (optional).
            timeout: Total loop timeout in seconds (default: 300.0).
            max_turns: Maximum agent loop iterations (default: 50).
            validation_retries: Max validation retry attempts for structured output.
            images: List of image URLs or file paths for vision models (optional).

        Returns:
            Response object. If response_format is provided, response.output
            contains the validated Pydantic model instance.
        """
        result = _run_sync(
            self.arun(
                prompt,
                response_format,
                max_output_tokens,
                temperature,
                timeout,
                max_turns,
                validation_retries,
                images,
            )
        )
        return cast("Response[T] | Response[str]", result)

    async def astream(
        self,
        prompt: str | None = None,
        response_format: type[T] | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> AsyncIterator[Event]:
        """
        Stream events asynchronously.

        Args:
            prompt: User prompt (optional if images provided).
            response_format: Pydantic model class for structured output (optional).
                            When provided, yields a StructuredOutputEvent with
                            the validated model after the respond tool is called.
            max_output_tokens: Maximum tokens in response (default: 8192).
            temperature: Sampling temperature (optional).
            timeout: Total loop timeout in seconds (default: 300.0).
            max_turns: Maximum agent loop iterations (default: 50).
            validation_retries: Max validation retry attempts for structured output.
            images: List of image URLs or file paths for vision models (optional).

        Yields:
            Event objects. If response_format is provided, includes a
            StructuredOutputEvent with the validated model.
        """
        # Handle structured output via response_format
        if response_format is not None:
            async for event in self._astream_structured(
                prompt=prompt,
                output_type=response_format,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                timeout=timeout,
                max_turns=max_turns,
                validation_retries=validation_retries,
                images=images,
            ):
                yield event
            return

        # Build user message content (handles images if provided)
        content = _build_user_content(prompt, images)
        user_msg = UserMessage(content=content)
        self.messages.append(user_msg)
        self._save_message(user_msg)

        # Build config
        config = self._make_config(max_output_tokens, temperature, timeout, max_turns)

        # Create tool context
        tool_context = ToolContext(
            workdir=self.workdir,
            session_id=self.session_id,
            model=self.model,
            tool_timeout=self.tool_timeout,
            temp_dir=self.temp_dir,  # Lazily created when first accessed
            read_paths=self.read_paths,
            write_paths=self.write_paths,
        )

        # Stream events
        async for event in loop_stream(
            provider=self._provider,
            messages=self.messages,
            tools=self.tools,
            config=config,
            context=tool_context,
            api_key=self.api_key,
            base_url=self.base_url,
            kits=self.kits,
        ):
            # Handle MessageEvent - save to session
            if isinstance(event, MessageEvent):
                self.messages.append(event.message)
                self._save_message(event.message)
            yield event

    async def _astream_structured(
        self,
        prompt: str | None,
        output_type: type[T],
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> AsyncIterator[Event]:
        """
        Internal method for streaming structured output with retry support.

        Streams events normally and yields a StructuredOutputEvent when
        the respond tool validation succeeds. Retries on validation failure.

        Messages are automatically saved via MessageEvent from the loop.
        """
        # Create respond tool and build tools list (without mutating self.tools)
        respond_tool = ResponseTool(output_type)
        tools_with_respond = [*self.tools, respond_tool]

        for attempt in range(validation_retries):
            # Use content on first attempt, empty on retries (session has context)
            # Images only on first attempt
            if attempt == 0:
                content = _build_user_content(prompt, images)
            else:
                content = ""

            # Track respond tool calls for validation
            pending_respond_calls: dict[str, dict[str, Any]] = {}  # id -> input

            # Add user message if content provided
            if content:
                user_msg = UserMessage(content=content)
                self.messages.append(user_msg)
                self._save_message(user_msg)

            # Build config
            config = self._make_config(
                max_output_tokens, temperature, timeout, max_turns
            )

            # Create tool context
            tool_context = ToolContext(
                workdir=self.workdir,
                session_id=self.session_id,
                model=self.model,
                tool_timeout=self.tool_timeout,
                temp_dir=self.temp_dir,  # Lazily created when first accessed
                read_paths=self.read_paths,
                write_paths=self.write_paths,
            )

            validation_failed = False
            respond_called = False

            # Stream events - let model use all tools freely
            # The model can call any tool (fetch, search, etc.) and should call
            # 'respond' when ready to produce structured output
            async for event in loop_stream(
                provider=self._provider,
                messages=self.messages,
                tools=tools_with_respond,
                config=config,
                context=tool_context,
                api_key=self.api_key,
                base_url=self.base_url,
                kits=self.kits,
                response_tool_name=respond_tool.name,  # Force on final turn
            ):
                yield event

                # Handle MessageEvent - save to session
                if isinstance(event, MessageEvent):
                    self.messages.append(event.message)
                    self._save_message(event.message)

                # Track respond tool calls for validation
                elif isinstance(event, ToolCallEvent) and event.name == "respond":
                    pending_respond_calls[event.id] = event.input

                # Check respond tool result for validation
                elif (
                    isinstance(event, ToolResultEvent) and event.tool_name == "respond"
                ):
                    respond_called = True
                    if not event.is_error:
                        # Get the input from the tracked tool call
                        input_data = pending_respond_calls.get(event.tool_use_id, {})
                        try:
                            validated = schema_validate(output_type, input_data)
                            yield StructuredOutputEvent(
                                output=validated,
                                success=True,
                            )
                            # Terminate stream on successful structured output
                            return
                        except Exception:
                            # Schema validation failed, mark for retry
                            validation_failed = True
                    else:
                        # Validation failed, mark for retry
                        validation_failed = True

            # If respond wasn't called or validation failed, retry if attempts remain
            if not respond_called or validation_failed:
                # Continue to next retry attempt
                continue

        # All retries exhausted
        yield StructuredOutputEvent(
            output=None,
            success=False,
        )

    def stream(
        self,
        prompt: str | None = None,
        response_format: type[T] | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_turns: int | None = None,
        validation_retries: int = 3,
        images: list[str | Path] | None = None,
    ) -> Iterator[Event]:
        """
        Stream events synchronously.

        Args:
            prompt: User prompt (optional if images provided).
            response_format: Pydantic model class for structured output (optional).
                            When provided, yields a StructuredOutputEvent with
                            the validated model after the respond tool is called.
            max_output_tokens: Maximum tokens in response (default: 8192).
            temperature: Sampling temperature (optional).
            timeout: Total loop timeout in seconds (default: 300.0).
            max_turns: Maximum agent loop iterations (default: 50).
            validation_retries: Max validation retry attempts for structured output.
            images: List of image URLs or file paths for vision models (optional).

        Yields:
            Event objects. If response_format is provided, includes a
            StructuredOutputEvent with the validated model.
        """
        # Use thread + queue for true sync streaming
        queue: Queue[Event | None] = Queue()
        exception_holder: list[Exception | None] = [None]

        def producer() -> None:
            try:
                event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(event_loop)
                try:

                    async def stream_events() -> None:
                        async for event in self.astream(
                            prompt,
                            response_format,
                            max_output_tokens,
                            temperature,
                            timeout,
                            max_turns,
                            validation_retries,
                            images,
                        ):
                            queue.put(event)
                        queue.put(None)  # Sentinel

                    event_loop.run_until_complete(stream_events())
                finally:
                    event_loop.close()
            except Exception as e:
                exception_holder[0] = e
                queue.put(None)

        thread = Thread(target=producer, daemon=True)
        thread.start()

        while True:
            item = queue.get()
            if item is None:
                # Check for exception before breaking
                if exception_holder[0]:
                    raise exception_holder[0]
                break
            if exception_holder[0]:
                raise exception_holder[0]
            yield item

    @contextlib.contextmanager
    def session(
        self,
    ) -> Generator[Any, None, None]:
        """
        Context manager for multi-turn conversations.

        Yields a callable that runs prompts within the same session.

        Example:
            with loop.session() as ask:
                ask("Remember this word: avocado")
                response = ask("What word did I ask you to remember?")
        """

        def ask(prompt: str, **kwargs: Any) -> Response[Any]:
            return self.run(prompt, **kwargs)

        # Add stream method to ask (dynamic attribute on function)
        ask.stream = lambda prompt, **kwargs: self.stream(prompt, **kwargs)

        yield ask

    @contextlib.asynccontextmanager
    async def asession(
        self,
    ) -> AsyncIterator[Any]:
        """
        Async context manager for multi-turn conversations.

        Yields a callable that runs prompts within the same session.

        Example:
            async with loop.asession() as ask:
                await ask("Remember this word: avocado")
                response = await ask("What word did I ask you to remember?")

                # Streaming also works within the session
                async for event in ask.astream("Tell me more"):
                    ...
        """

        async def ask(prompt: str, **kwargs: Any) -> Response[Any]:
            return await self.arun(prompt, **kwargs)

        # Add astream method to ask (dynamic attribute on function)
        ask.astream = lambda prompt, **kwargs: self.astream(prompt, **kwargs)

        yield ask


@overload
def run(
    prompt: str,
    model: str,
    response_format: None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
    max_turns: int | None = None,
    validation_retries: int = 3,
    **kwargs: Any,
) -> Response[str]: ...


@overload
def run(
    prompt: str,
    model: str,
    response_format: type[T],
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
    max_turns: int | None = None,
    validation_retries: int = 3,
    **kwargs: Any,
) -> Response[T]: ...


def run(
    prompt: str,
    model: str,
    response_format: type[T] | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
    max_turns: int | None = None,
    validation_retries: int = 3,
    **kwargs: Any,
) -> Response[T] | Response[str]:
    """
    One-shot helper for running a prompt.

    Args:
        prompt: User prompt.
        model: Model string (e.g., "anthropic/claude-sonnet-4").
        response_format: Pydantic model class for structured output (optional).
        max_output_tokens: Maximum tokens in response (default: 8192).
        temperature: Sampling temperature (optional).
        timeout: Total loop timeout in seconds (default: 300.0).
        max_turns: Maximum agent loop iterations (default: 50).
        validation_retries: Max validation retry attempts for structured output.
        **kwargs: Additional Loop arguments (tools, system, workdir, etc.).

    Returns:
        Response object. If response_format is provided, response.output
        contains the validated Pydantic model instance.
    """
    return Loop(model=model, **kwargs).run(
        prompt,
        response_format=response_format,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        timeout=timeout,
        max_turns=max_turns,
        validation_retries=validation_retries,
    )


@overload
async def arun(
    prompt: str,
    model: str,
    response_format: None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
    max_turns: int | None = None,
    validation_retries: int = 3,
    **kwargs: Any,
) -> Response[str]: ...


@overload
async def arun(
    prompt: str,
    model: str,
    response_format: type[T],
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
    max_turns: int | None = None,
    validation_retries: int = 3,
    **kwargs: Any,
) -> Response[T]: ...


async def arun(
    prompt: str,
    model: str,
    response_format: type[T] | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
    max_turns: int | None = None,
    validation_retries: int = 3,
    **kwargs: Any,
) -> Response[T] | Response[str]:
    """
    One-shot async helper for running a prompt.

    Args:
        prompt: User prompt.
        model: Model string (e.g., "anthropic/claude-sonnet-4").
        response_format: Pydantic model class for structured output (optional).
        max_output_tokens: Maximum tokens in response (default: 8192).
        temperature: Sampling temperature (optional).
        timeout: Total loop timeout in seconds (default: 300.0).
        max_turns: Maximum agent loop iterations (default: 50).
        validation_retries: Max validation retry attempts for structured output.
        **kwargs: Additional Loop arguments (tools, system, workdir, etc.).

    Returns:
        Response object. If response_format is provided, response.output
        contains the validated Pydantic model instance.
    """
    return await Loop(model=model, **kwargs).arun(
        prompt,
        response_format=response_format,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        timeout=timeout,
        max_turns=max_turns,
        validation_retries=validation_retries,
    )


def stream(
    prompt: str | None = None,
    model: str = "",
    response_format: type[T] | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
    max_turns: int | None = None,
    validation_retries: int = 3,
    images: list[str | Path] | None = None,
    **kwargs: Any,
) -> Iterator[Event]:
    """
    One-shot helper for streaming events.

    Args:
        prompt: User prompt (optional if images provided).
        model: Model string (e.g., "anthropic/claude-sonnet-4").
        response_format: Pydantic model class for structured output (optional).
        max_output_tokens: Maximum tokens in response (default: 8192).
        temperature: Sampling temperature (optional).
        timeout: Total loop timeout in seconds (default: 300.0).
        max_turns: Maximum agent loop iterations (default: 50).
        validation_retries: Max validation retry attempts for structured output.
        images: List of image URLs or file paths for vision models (optional).
        **kwargs: Additional Loop arguments (tools, system, workdir, etc.).

    Yields:
        Event objects. If response_format is provided, includes a
        StructuredOutputEvent with the validated model.
    """
    yield from Loop(model=model, **kwargs).stream(
        prompt,
        response_format=response_format,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        timeout=timeout,
        max_turns=max_turns,
        validation_retries=validation_retries,
        images=images,
    )


async def astream(
    prompt: str | None = None,
    model: str = "",
    response_format: type[T] | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
    max_turns: int | None = None,
    validation_retries: int = 3,
    images: list[str | Path] | None = None,
    **kwargs: Any,
) -> AsyncIterator[Event]:
    """
    One-shot async helper for streaming events.

    Args:
        prompt: User prompt (optional if images provided).
        model: Model string (e.g., "anthropic/claude-sonnet-4").
        response_format: Pydantic model class for structured output (optional).
        max_output_tokens: Maximum tokens in response (default: 8192).
        temperature: Sampling temperature (optional).
        timeout: Total loop timeout in seconds (default: 300.0).
        max_turns: Maximum agent loop iterations (default: 50).
        validation_retries: Max validation retry attempts for structured output.
        images: List of image URLs or file paths for vision models (optional).
        **kwargs: Additional Loop arguments (tools, system, workdir, etc.).

    Yields:
        Event objects. If response_format is provided, includes a
        StructuredOutputEvent with the validated model.
    """
    async for event in Loop(model=model, **kwargs).astream(
        prompt,
        response_format=response_format,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        timeout=timeout,
        max_turns=max_turns,
        validation_retries=validation_retries,
        images=images,
    ):
        yield event


__all__ = ["Loop", "run", "arun", "stream", "astream"]
