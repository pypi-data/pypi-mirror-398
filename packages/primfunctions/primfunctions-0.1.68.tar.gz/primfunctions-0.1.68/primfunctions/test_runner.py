import uuid
import pytest

from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    Tuple,
    Union,
    Dict,
)

from .context import Context
from .configuration import Configuration
from .events import (
    Event,
    StartEvent,
    TextEvent,
    TimeoutEvent,
    StopEvent,
    ErrorEvent,
    TextToSpeechEvent,
)


HandlerType = Callable[[Event, Context], Awaitable[Any]]
EventInput = Union[Event, str]


class TestRunner:
    """
    TestRunner for testing VoiceRun agent handlers with pytest.

    A handler is the async function you export in your agent. It receives an Event
    and a Context, and yields zero or more Events as output.

    Basic Usage with pytest:
        # Define your handler
        async def my_handler(event: Event, context: Context):
            if isinstance(event, StartEvent):
                yield TextToSpeechEvent(text="Hello! How can I help?")
            elif isinstance(event, TextEvent):
                user_text = event.data["text"]
                yield TextToSpeechEvent(text=f"You said: {user_text}")

        # Create a handler fixture
        @pytest.fixture
        def handler():
            return my_handler

        # Write your test
        @pytest.mark.asyncio
        async def test_greeting(runner, handler):
            runner.handler = handler
            await runner.start()

            # Use pytest assertions
            assert "Hello" in runner.get_tts_texts()
            assert runner.has_event_type(TextToSpeechEvent)

            # Test user input
            await runner.text("hello world")
            assert "You said: hello world" in runner.get_tts_texts()

        # Or use create_test_runner() directly
        @pytest.mark.asyncio
        async def test_direct():
            runner = create_test_runner(my_handler)
            await runner.start()
            assert len(runner.get_tts_events()) == 1
    """

    def __init__(
        self,
        handler: HandlerType,
        *,
        context: Context | None = None,
        agent_id: str = "",
        environment: str = "",
        configuration: Configuration | None = None,
        variables: Dict[str, Any] | None = None,
        data: Dict[str, Any] | None = None,
        session_id: str | None = None,
    ):
        self.handler: HandlerType = handler

        self._captured_events: list[Event] = []
        self._captured_debug: list[Tuple[Event, str, dict]] = []
        self._turn: int = 0

        if context is None:
            configuration = configuration or Configuration()
            variables = variables or {}
            data = data or {}
            session_id = session_id or str(uuid.uuid4())

            def _on_event(e: Event):
                self._emit(e)

            def _on_debug_event(e: Event, direction: str, ctx: dict):
                self._captured_debug.append((e, direction, ctx))

            self.context = Context(
                agent_id=agent_id,
                environment=environment,
                session_id=session_id,
                configuration=configuration,
                data=data,
                variables=variables,
                on_event=_on_event,
                on_debug_event=_on_debug_event,
            )
        else:

            def _on_event(e: Event):
                self._emit(e)

            def _on_debug_event(e: Event, direction: str, ctx: dict):
                self._captured_debug.append((e, direction, ctx))

            context.on_event = _on_event
            context.on_debug_event = _on_debug_event
            self.context = context

    # ---------- Core execution ----------
    async def send(self, event: Event, *, wait_background: bool = False) -> list[Event]:
        """
        Send one input Event to the handler and return all output Events emitted for this turn.
        Set wait_background=True to wait for any background tasks spawned during this turn.
        """
        self._turn += 1
        event.turn = self._turn

        before_count = len(self._captured_events)

        result = self.handler(event, self.context)

        if hasattr(result, "__aiter__"):
            async for output in result:
                self._emit(output)
        else:
            await result  # type: ignore[arg-type]

        if wait_background:
            await self.context.wait_for_all_tasks()

        return self._captured_events[before_count:]

    async def start(self, *, wait_background: bool = False) -> list[Event]:
        """
        Reset the runner state and send a StartEvent.
        """
        self.reset()

        return await self.send(StartEvent(), wait_background=wait_background)

    async def text(
        self, message: str, source: str = "text", *, wait_background: bool = False
    ) -> list[Event]:
        return await self.send(
            TextEvent(source=source, text=message), wait_background=wait_background
        )

    async def timeout(
        self,
        count: int = 1,
        ms_since_input: int = 5000,
        *,
        wait_background: bool = False,
    ) -> list[Event]:
        return await self.send(
            TimeoutEvent(count=count, ms_since_input=ms_since_input),
            wait_background=wait_background,
        )

    async def stop(self, *, wait_background: bool = False) -> list[Event]:
        return await self.send(StopEvent(), wait_background=wait_background)

    async def run(
        self, inputs: Iterable[EventInput], *, wait_background: bool = False
    ) -> list[Event]:
        """
        Run a sequence of inputs. Strings are treated as TextEvent(user input).
        Returns all outputs produced across the sequence.
        """
        start_index = len(self._captured_events)
        for item in inputs:
            if isinstance(item, str):
                await self.text(item, wait_background=wait_background)
            elif isinstance(item, Event):
                await self.send(item, wait_background=wait_background)
            else:
                raise TypeError("Inputs must be Event or str")
        return self._captured_events[start_index:]

    async def run_dialogue(
        self, *inputs: EventInput, wait_background: bool = False
    ) -> list[Event]:
        """
        Sugar for run(); accepts variadic inputs.
        """
        return await self.run(inputs, wait_background=wait_background)

    @property
    def captured_events(self) -> list[Event]:
        return self._captured_events

    @property
    def captured_debug(self) -> list[Tuple[Event, str, dict]]:
        return self._captured_debug

    def last_turn_events(self) -> list[Event]:
        return [e for e in self._captured_events if e.turn == self._turn]

    def events_by_turn(self) -> dict[int, list[Event]]:
        by_turn: dict[int, list[Event]] = {}
        for e in self._captured_events:
            by_turn.setdefault(e.turn, []).append(e)
        return by_turn

    def get_tts_texts(self) -> list[str]:
        """
        Get all text content from TextToSpeechEvent outputs.

        Returns:
            List of text strings from all TTS events.
        """
        texts: list[str] = []
        for e in self._captured_events:
            if e.name == "text_to_speech":
                text = (e.data or {}).get("text", "")
                if isinstance(text, str):
                    texts.append(text)
        return texts

    def get_tts_events(self) -> list[TextToSpeechEvent]:
        """
        Get all TextToSpeechEvent outputs.

        Returns:
            List of TextToSpeechEvent objects.
        """
        return [e for e in self._captured_events if isinstance(e, TextToSpeechEvent)]

    def get_events_by_type(self, event_type: type[Event]) -> list[Event]:
        """
        Get all events of a specific type.

        Args:
            event_type: The Event subclass to filter by.

        Returns:
            List of matching events.
        """
        return [e for e in self._captured_events if isinstance(e, event_type)]

    def get_events_by_name(self, event_name: str) -> list[Event]:
        """
        Get all events with a specific name.

        Args:
            event_name: The event name to filter by (e.g., "text_to_speech").

        Returns:
            List of matching events.
        """
        return [e for e in self._captured_events if e.name == event_name]

    def has_event_type(self, event_type: type[Event]) -> bool:
        """
        Check if any event of the given type was emitted.

        Args:
            event_type: The Event subclass to check for.

        Returns:
            True if at least one matching event exists.
        """
        return any(isinstance(e, event_type) for e in self._captured_events)

    def has_event_name(self, event_name: str) -> bool:
        """
        Check if any event with the given name was emitted.

        Args:
            event_name: The event name to check for.

        Returns:
            True if at least one matching event exists.
        """
        return any(e.name == event_name for e in self._captured_events)

    def get_last_tts_text(self) -> str | None:
        """
        Get the text from the most recent TextToSpeechEvent.

        Returns:
            The text string, or None if no TTS events were emitted.
        """
        tts_events = self.get_tts_events()
        if not tts_events:
            return None
        return tts_events[-1].data.get("text", "")

    # Simple assertion helpers that work with pytest's assertion introspection
    def expect_any_tts_contains(self, substring: str):
        """
        Assert that at least one TextToSpeechEvent contains the given substring.

        This raises AssertionError with a helpful message if the assertion fails.
        Works with pytest's assertion introspection for better error messages.

        Args:
            substring: The substring to search for in TTS texts.

        Raises:
            AssertionError: If no TTS event contains the substring.
        """
        texts = self.get_tts_texts()
        if not any(substring in t for t in texts):
            raise AssertionError(
                f"No TextToSpeechEvent contained substring: {substring!r}. "
                f"Got {len(texts)} TTS events with texts: {texts}"
            )

    def expect_event_types_in_last_turn(self, expected_types: list[str]):
        """
        Assert that the last turn emitted events matching the expected types.

        Args:
            expected_types: List of event names expected in the last turn.

        Raises:
            AssertionError: If the event types don't match.
        """
        names = [e.name for e in self.last_turn_events()]
        if names != expected_types:
            raise AssertionError(
                f"Unexpected events for turn {self._turn}. "
                f"Expected {expected_types}, got {names}"
            )

    def expect_no_errors(self):
        """
        Assert that no ErrorEvent was emitted.

        Raises:
            AssertionError: If any ErrorEvent was emitted.
        """
        errors = self.get_events_by_type(ErrorEvent)
        if errors:
            error_messages = [e.data.get("message", "") for e in errors]
            raise AssertionError(
                f"Expected no errors, but {len(errors)} error(s) were emitted: {error_messages}"
            )

    def _emit(self, event: Event):
        if not getattr(event, "turn", None):
            event.turn = self._turn
        self._captured_events.append(event)

    def reset(self):
        """
        Reset the test runner state, clearing all captured events.

        Useful for testing multiple scenarios in the same test.
        """
        self._captured_events.clear()
        self._captured_debug.clear()
        self._turn = 0


def create_test_runner(
    handler: HandlerType,
    *,
    context: Context | None = None,
    agent_id: str = "",
    environment: str = "",
    configuration: Configuration | None = None,
    variables: Dict[str, Any] | None = None,
    data: Dict[str, Any] | None = None,
    session_id: str | None = None,
) -> TestRunner:
    """
    Factory function to create a TestRunner instance.

    This is useful when you need to create a runner outside of a pytest fixture.

    Args:
        handler: The async handler function to test.
        context: Optional Context instance. If not provided, one will be created.
        agent_id: Agent identifier for the context.
        environment: Environment name for the context.
        configuration: Optional Configuration instance.
        variables: Optional dictionary of context variables.
        data: Optional dictionary of context data.
        session_id: Optional session ID. If not provided, a UUID will be generated.

    Returns:
        A configured TestRunner instance.

    Example:
        async def my_handler(event: Event, context: Context):
            yield TextToSpeechEvent(text="Hello")

        runner = create_test_runner(my_handler)
        await runner.start()
    """
    return TestRunner(
        handler,
        context=context,
        agent_id=agent_id,
        environment=environment,
        configuration=configuration,
        variables=variables,
        data=data,
        session_id=session_id,
    )


if pytest:

    @pytest.fixture
    def runner(request):
        """
        Pytest fixture that creates a TestRunner.

        To use this fixture, you need to provide a handler. The recommended approach
        is to create a handler fixture and use it with the runner:

        Example:
            @pytest.fixture
            def handler():
                async def my_handler(event: Event, context: Context):
                    if isinstance(event, StartEvent):
                        yield TextToSpeechEvent(text="Hello!")
                    elif isinstance(event, TextEvent):
                        yield TextToSpeechEvent(text=f"You said: {event.data['text']}")
                return my_handler

            @pytest.mark.asyncio
            async def test_my_handler(runner, handler):
                runner.handler = handler
                await runner.start()
                assert "Hello" in runner.get_tts_texts()

                await runner.text("test")
                assert "You said: test" in runner.get_tts_texts()

        Alternatively, use create_test_runner() directly in your test:

        Example:
            @pytest.mark.asyncio
            async def test_with_create(runner):
                async def my_handler(event, context):
                    yield TextToSpeechEvent(text="Hi")

                runner.handler = my_handler
                await runner.start()
        """
        handler = None

        if hasattr(request, "param") and callable(request.param):
            handler = request.param
        elif "handler" in request.fixturenames:
            try:
                handler = request.getfixturevalue("handler")
            except Exception:
                pass

        if handler is None:

            async def _dummy_handler(event: Event, context: Context):
                raise ValueError(
                    "No handler provided. Either:\n"
                    "1. Create a 'handler' fixture and pass it to your test\n"
                    "2. Set runner.handler = my_handler in your test\n"
                    "3. Use create_test_runner(my_handler) to create a runner manually"
                )

            handler = _dummy_handler

        return TestRunner(handler)
