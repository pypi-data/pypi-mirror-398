import json
import traceback
import os
from datetime import datetime, timezone


class Event:
    """Base event class for all system events.

    Args:
        name: The name of the event
        data: Optional dictionary containing event-specific data
        timestamp: ISO format timestamp, defaults to current UTC time if not provided
        turn: The turn number of the event, defaults to 0
        background: Whether the event is a background task, defaults to False
        background_task_name: The name of the background task, defaults to None
    Attributes:
        name: The event name
        data: Event data dictionary
        timestamp: ISO format timestamp string
        turn: The turn number of the event
        background: Whether the event is a background task, defaults to False
        background_task_name: The name of the background task, defaults to None
    """

    def __init__(
        self,
        name: str,
        data: dict = {},
        timestamp: str | None = None,
        turn: int = 0,
        background: bool = False,
        background_task_name: str = None,
    ):
        self.name = name
        self.data = data
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.turn = turn
        self.background = background
        self.background_task_name = background_task_name


class CustomEvent(Event):
    """Custom event with additional custom flag in data.

    This event is used for creating custom events that can be identified
    in the debugger with a custom flag. Useful for client-specific events
    in projects that leverage prim-ai-engine and prim-ai-functions.

    Args:
        name: The name of the custom event
        data: Optional dictionary containing event-specific data
    """

    def __init__(self, name: str, data: dict = {}):
        super().__init__(name, {**data, "custom": True})


class StartEvent(Event):
    """Event emitted when a new voice agent session has started.

    This event marks the beginning of a voice agent session and can be used
    to initialize session state or perform startup operations.
    """

    def __init__(self):
        super().__init__("start")


class StopEvent(Event):
    """Stops the current voice agent session. This will end the call.

    When emitted, this event terminates the active voice agent session
    and ends the call connection. Optionally plays a closing message
    before ending the call.

    Args:
        closing_speech: Optional text to speak before ending the call
        voice: Voice to use for closing speech (defaults to agent's default voice)
        speed: Playback speed for closing speech (0.25x-4.0x, defaults to 1.0)
        language: Language code for closing speech (defaults to "en")
    """

    def __init__(
        self,
        closing_speech: str | None = None,
        voice: str | None = None,
        speed: float = 1.0,
        language: str = "en",
    ):
        data = {
            "closing_speech": closing_speech,
            "voice": voice,
            "speed": speed,
            "language": language,
        }
        super().__init__("stop", data)


class InterruptEvent(Event):
    """Event for interrupting current audio in the queue.

    This event is not emitted when an interrupt occurs by the user,
    but rather is emitted by the developer to interrupt any current
    audio in the queue. May be used in future implementations.
    """

    def __init__(self):
        super().__init__("interrupt")


class TimeoutEvent(Event):
    """Event emitted when the user does not speak for a specified duration.

    This timeout event helps detect periods of user inactivity and can
    be used to prompt the user or take appropriate action.

    Args:
        count: Number of timeouts in a row that have occurred, defaults to 0
        ms_since_input: Milliseconds since last input, defaults to 0
    """

    def __init__(self, count: int = 0, ms_since_input: int = 0):
        super().__init__("timeout", {"count": count, "ms_since_input": ms_since_input})


class TextEvent(Event):
    """Event emitted when the user speaks or types text.

    This event captures user input in text form, whether it comes from
    speech-to-text conversion or direct text input.

    Args:
        source: The source of the text event (e.g. "speech", "text")
        text: The text content spoken or typed by the user
        language: The language of the text (optionally provided by model)
    """

    def __init__(self, source: str, text: str, language: str | None = None):
        super().__init__("text", {"source": source, "text": text, "language": language})


class TextToSpeechEvent(Event):
    """Converts text to speech using the specified voice and plays it to the user.

    Supports multiple voice providers including OpenAI, Prim, Google Chirp,
    Azure, and Cartesia voices. Voice-specific features like instructions
    and speed control vary by provider.

    Args:
        text: The text content to be converted to speech
        voice: Voice to use for synthesis. Available voices include:
            - OpenAI (9 voices): alloy, ash, coral, echo, fable, onyx, nova, sage, shimmer
            - Prim (6 voices): breath, flint, juniper, atlas, solstice, lyric
            - Google Chirp (30 voices): zephyr, puck, charon, kore, fenrir, etc.
            - Azure (32 voices): xiaoxiao, xiaoxiao-multilingual, hsiaochen, etc.
            - Cartesia (10 voices): brooke, david, sophie, luke, etc.
            Defaults to "nova"
        cache: Whether to cache the generated audio, defaults to True
        interruptible: Whether the speech can be interrupted, defaults to None
        instructions: Optional voice styling instructions to control tone, emotion,
            or accent (e.g., 'enthusiastic with a Taiwanese accent').
            Supported by OpenAI voices only
        speed: Optional playback speed modifier ranging from 0.25x to 4.0x.
            Supported by OpenAI (0.25x-4.0x) and Azure (0.5x-3.0x) voices.
            Defaults to 1.0
        language: Optional language code for the speech, defaults to "en"
        stream: Optional streaming configuration (tri-state support)
    """

    def __init__(
        self,
        text: str,
        voice="nova",
        cache=True,
        interruptible: bool = None,
        instructions="",
        speed=1.0,
        language="en",
        stream=None,
    ):
        data = {
            "text": text,
            "voice": voice,
            "cache": cache,
            "interruptible": interruptible,
            "instructions": instructions,
            "speed": speed,
            "language": language,
        }

        # Only include stream if explicitly provided (tri-state support)
        if stream is not None:
            data["stream"] = stream

        super().__init__("text_to_speech", data)


class AudioEvent(Event):
    """Plays audio to the user from a URL.

    This event streams audio content from a specified URL to the user.
    The audio file should be accessible via HTTP/HTTPS.

    Args:
        path: The URL of the audio file to play
    """

    def __init__(self, path: str):
        super().__init__("audio", {"path": path})


class SilenceEvent(Event):
    """Plays silence for a specified duration in milliseconds.

    This event creates a pause in the conversation by playing silence
    for the specified duration, useful for creating natural breaks.

    Args:
        duration: The duration of silence in milliseconds
    """

    def __init__(self, duration: int):
        super().__init__("silence", {"duration": duration})


class ContextUpdateEvent(Event):
    """Updates the conversation context with new information.

    This event is for internal use only. It is the last event emitted by
    the function handler when run in the sandbox in HTTP mode, acting as
    a way to pass context between the engine and the sandbox. When moving
    to WebSockets, this becomes unnecessary as context remains in the
    sandbox for the lifetime of the WebSocket.

    Args:
        context: Dictionary containing context updates to apply
    """

    def __init__(self, context: dict):
        super().__init__("context", {"context": context})


class ErrorEvent(Event):
    """Event emitted when an error occurs in the system.

    This event signals that an error condition has been encountered
    and provides details about the error for logging or handling.

    Args:
        message: The error message describing what went wrong
    """

    def __init__(self, message: str):
        super().__init__("error", {"message": message})


class LogEvent(Event):
    """Logs a message to the system logs.

    This event creates a log entry with the specified message and file/line number where it is triggered from,
    useful for debugging, monitoring, and tracking system behavior.

    Args:
        message: The message to log
    """

    def __init__(self, message: str, location: str = None):
        super().__init__("log", {"message": message})

        # If location is provided, use it. Otherwise, try to calculate it
        if location:
            self.data["location"] = location
        else:
            calculated_location = self._capture_user_location()
            if calculated_location:
                self.data["location"] = calculated_location

    def _capture_user_location(self):
        """Capture the location where this LogEvent was created in user code."""
        # Get the call stack
        stack = traceback.extract_stack()

        # Look for the first frame that's user code (not infrastructure)
        for frame in reversed(stack):
            filename = frame.filename
            basename = os.path.basename(filename)

            # Skip infrastructure files
            if any(
                skip in filename
                for skip in [
                    "runtime.py",  # Our runtime
                    "site-packages",  # Python packages
                    "__pycache__",  # Cached Python files
                    "asyncio",  # Python async machinery
                    "generator",  # Generator infrastructure
                    "events.py",  # Event processing infrastructure
                ]
            ):
                continue

            # Skip absolute system paths
            if filename.startswith("/usr/") or filename.startswith("/System/"):
                continue

            # Found user code!
            if basename.endswith(".py"):
                return f"{basename}:{frame.lineno}"

        # Enhanced fallback: search deeper in stack
        for i in range(3, min(len(stack), 10)):
            frame = stack[-i]
            filename = frame.filename
            basename = os.path.basename(filename)

            if (
                basename.endswith(".py")
                and "site-packages" not in filename
                and not filename.startswith("/usr/")
                and not filename.startswith("/System/")
            ):
                return f"{basename}:{frame.lineno}"

        return None


class CollectPaymentEvent(Event):
    """Event for collecting payment from the user.

    This event initiates a payment collection process with the specified amount.

    Args:
        amount: The payment amount to collect
    """

    def __init__(self, amount: float):
        super().__init__("collect_payment", {"amount": amount})


class CollectPaymentSuccessEvent(Event):
    """Event emitted when payment collection is successful.

    This event confirms that a payment has been successfully processed
    and collected from the user.
    """

    def __init__(self):
        super().__init__("collect_payment_success")


class SupervisorRequestEvent(Event):
    """Event for requesting supervisor assistance in speech-to-speech mode.

    This event is used with the speech-to-speech model when the model
    calls for help from a supervisor. This is a work-in-progress feature
    and may change in future implementations.

    Args:
        content: The content describing the supervisor request
    """

    def __init__(self, content: str):
        super().__init__("supervisor_request", {"content": content})


class SupervisorResponseEvent(Event):
    """Event containing supervisor response in speech-to-speech mode.

    This event is emitted by the handler to update the context of the
    speech-to-speech model with supervisor responses. This is a
    work-in-progress feature and may change in future implementations.

    Args:
        content: The supervisor's response content
    """

    def __init__(self, content: str):
        super().__init__("supervisor_response", {"content": content})


class ConnectSTSEvent(Event):
    """Event for connecting to Speech-to-Speech service.

    This event establishes a connection to the Speech-to-Speech (STS)
    service with the provided configuration parameters. This is a
    work-in-progress feature and may change in future implementations.

    Args:
        configuration: Dictionary containing STS connection configuration
    """

    def __init__(self, configuration: dict):
        super().__init__("connect_sts", {"configuration": configuration})


class DisconnectSTSEvent(Event):
    """Event for disconnecting from Speech-to-Speech service.

    This event terminates the connection to the Speech-to-Speech (STS)
    service and cleans up associated resources. This is a
    work-in-progress feature and may change in future implementations.
    """

    def __init__(self):
        super().__init__("disconnect_sts", {})


class UpdateCallEvent(Event):
    """Event for updating call parameters in telephony provider.

    This event updates the call in the telephony provider.
    For example, it can be used to update the TwiML or other call settings
    during an active call session.

    Args:
        data: Dictionary containing call update data
    """

    def __init__(self, data: dict):
        super().__init__("update_call", {"data": data})


class StartRecordingEvent(Event):
    """Event for starting call recording.

    This event initiates recording of the current call, with an optional
    callback URL for recording status updates.

    Args:
        status_callback_url: Optional URL for recording status callbacks
    """

    def __init__(self, status_callback_url: str = None):
        super().__init__(
            "start_recording", {"status_callback_url": status_callback_url}
        )


class StopRecordingEvent(Event):
    """Event for stopping call recording.

    This event terminates the current call recording and finalizes
    the recorded audio file.
    """

    def __init__(self):
        super().__init__("stop_recording")


class STTUpdateSettingsEvent(Event):
    """Dynamically updates Speech-to-Text (STT) configuration settings during a conversation.

    This allows agents to change language, transcription prompts, and endpointing
    sensitivity without restarting the session. Useful for multilingual conversations
    or adjusting to different conversation contexts.

    Args:
        language: The language code for transcription. Examples: 'en' (English),
            'es' (Spanish), 'fr' (French), 'de' (German), 'ja' (Japanese),
            'zh' (Chinese), 'multi' (automatic language detection)
        prompt: Context prompt to improve transcription accuracy. Examples:
            'This is a technical conversation about software development',
            'Medical terminology and patient care discussion'
        endpointing: Controls when the system considers the user has finished speaking.
            Values: >3 (Server VAD with silence duration in milliseconds),
            3 (Semantic VAD 'high' eagerness), 2 (Semantic VAD 'medium' eagerness),
            1 (Semantic VAD 'low' eagerness), 0 (Semantic VAD 'auto' eagerness)
        noise_reduction_type: Type of noise reduction to apply
        model: STT model to use for transcription
    """

    def __init__(
        self,
        language: str = None,
        prompt: str = None,
        endpointing: int = None,
        noise_reduction_type: str = None,
        model: str = None,
    ):
        super().__init__(
            "stt_update_settings",
            {
                "language": language,
                "prompt": prompt,
                "endpointing": endpointing,
                "noise_reduction_type": noise_reduction_type,
                "model": model,
            },
        )


class STTModelSwitchedEvent(Event):
    """Event emitted when STT model has been switched.

    This event provides information about STT model transitions,
    including timing metrics for the switch operation.

    Args:
        from_model: The previous STT model that was in use
        to_model: The new STT model that is now active
        warmup_ms: Time in milliseconds taken to warm up the new model
        switch_delay_ms: Delay in milliseconds during the model switch
    """

    def __init__(
        self,
        from_model: str | None,
        to_model: str | None,
        warmup_ms: int = 0,
        switch_delay_ms: int = 0,
    ):
        payload = {
            "from_model": from_model,
            "to_model": to_model,
            "warmup_ms": warmup_ms,
            "switch_delay_ms": switch_delay_ms,
        }
        super().__init__("stt_model_switched", payload)


class TurnEndEvent(Event):
    """Event emitted when a conversation turn ends.

    This event is for internal use only. It marks the completion of
    a turn in the conversation, providing duration metrics for analysis.

    Args:
        duration: Duration of the turn in milliseconds
    """

    def __init__(self, duration: int):
        super().__init__("turn_end", {"duration": duration})


class TurnInterruptedEvent(Event):
    """Event emitted when a conversation turn is interrupted.

    This event is for internal use only. It indicates that the current
    turn was cut short, typically due to user input or system conditions.
    """

    def __init__(self):
        super().__init__("turn_interrupted")


class InitializeEvent(Event):
    """Event for initializing an agent session.

    This event is for internal use only. It sets up a new agent session
    with code, configuration, and context information.

    Args:
        code: The agent code to initialize
        hash: Hash of the agent code for verification
        is_multifile: Whether the agent uses multiple files
        is_debug: Whether debug mode is enabled
        context: Initial context dictionary for the session
        tracing_enabled: Whether tracing is enabled
    """

    def __init__(
        self,
        code: str,
        hash: str,
        is_multifile: bool,
        is_debug: bool,
        context: dict,
        tracing_enabled: bool,
    ):
        super().__init__(
            "initialize",
            {
                "code": code,
                "hash": hash,
                "is_multifile": is_multifile,
                "is_debug": is_debug,
                "context": context,
                "tracing_enabled": tracing_enabled,
            },
        )


class HandlerEndEvent(Event):
    """Event for when a handler is finished.

    This event is for internal use only. It is used to indicate that a handler has finished.
    """

    def __init__(self):
        super().__init__("handler_end")


class TestingEvent(Event):
    """Event for testing purposes.

    This event is for internal use only. It is used during testing
    and development to inject test data or trigger test scenarios.

    Args:
        data: Dictionary containing test data
    """

    def __init__(self, data: dict):
        super().__init__("testing", {"data": data})


class DebugEvent(Event):
    """Event for debugging information.

    This event is for internal use only. It is used in the WebSocket
    implementation to tell the engine to push debug frames to the
    front end so they display in the function debugger.

    Args:
        event_name: Name of the event being debugged
        event_data: Data from the event being debugged
        direction: Direction of the event (e.g., 'input', 'output')
        context: Additional context for debugging
    """

    def __init__(
        self, event_name: str, event_data: dict, direction: str, context: dict
    ):
        super().__init__(
            "debug",
            {
                "event_name": event_name,
                "event_data": event_data,
                "direction": direction,
                "context": context,
            },
        )


class MetricEvent(Event):
    """Event for collecting metrics data.

    This event captures various types of metrics including latency,
    count, gauge, and ratio measurements for system monitoring.

    Args:
        metric_type: Type of metric - one of "latency", "count", "gauge", "ratio"
        name: Name of the metric being measured
        data: Dictionary containing metric-specific data
    """

    def __init__(self, metric_type: str, name: str, data: dict = {}):
        # metric_type: one of "latency", "count", "gauge", "ratio"
        event_name = f"metrics.{metric_type}.{name}"
        super().__init__(event_name, data or {})


class SessionEndEvent(Event):
    """Event emitted when an agent session ends.

    This event marks the termination of an agent session and
    can be used for cleanup or final processing.
    """

    def __init__(self):
        super().__init__("session_end")


class StartSessionEvent(Event):
    """Event for starting a new agent session.

    This event initializes a new session with the specified agent
    and configuration parameters.

    Args:
        agent_id: Identifier of the agent to start
        environment: Environment configuration for the session
        input_type: Type of input the session will handle
        input_parameters: Parameters specific to the input type
        parameters: General session parameters
    """

    def __init__(
        self,
        agent_id: str = "",
        environment: str = "",
        input_type: str = "",
        input_parameters: dict = {},
        parameters: dict = {},
    ):
        super().__init__(
            "start_session",
            {
                "agent_id": agent_id,
                "environment": environment,
                "input_type": input_type,
                "input_parameters": input_parameters,
                "parameters": parameters,
            },
        )


class MergeSessionEvent(Event):
    """Event for merging sessions.

    This event combines the current session with another session
    identified by the provided session ID.

    Args:
        session_id: ID of the session to merge with
    """

    def __init__(self, session_id: str):
        super().__init__(
            "merge_session",
            {
                "session_id": session_id,
            },
        )


class TransferSessionEvent(Event):
    """Channel-agnostic session transfer request.

    For phone sessions:
      - if phone_number provided -> transfer to that number (cold)
      - if warm and phone_number provided -> warm transfer with data

    For web/mic/api sessions:
      - if agent_id provided -> browser redirect to target agent/environment

    Args:
        phone_number: Phone number to transfer to (for phone sessions)
        agent_id: Agent ID to transfer to (for web/mic/api sessions)
        environment: Environment to transfer to
        data: Additional data to pass to the transferred session
        closing_speech: Optional text to speak before transferring
        voice: Voice to use for closing speech (defaults to agent's default voice)
        speed: Playback speed for closing speech (0.25x-4.0x, defaults to 1.0)
        language: Language code for closing speech (defaults to "en")
    """

    def __init__(
        self,
        *,
        phone_number: str | None = None,
        agent_id: str | None = None,
        environment: str | None = None,
        data: dict | None = None,
        closing_speech: str | None = None,
        voice: str | None = None,
        speed: float = 1.0,
        language: str = "en",
    ):
        payload = {
            "phone_number": phone_number,
            "agent_id": agent_id,
            "environment": environment,
            "data": data or {},
            "closing_speech": closing_speech,
            "voice": voice,
            "speed": speed,
            "language": language,
        }
        super().__init__("transfer_session", payload)


class TranscriptPartEvent(Event):
    """Event for a transcript part.

    This event is for internal use only. It is used to store transcript parts.

    Args:
        role: The role of the transcript part
        content: The content of the transcript part
    """

    def __init__(self, role: str, content: str):
        super().__init__(
            "transcript_part",
            {
                "role": role,
                "content": content,
            },
        )


class InputAllowedEvent(Event):
    """Event to enable or disable user input.

    InputAllowedEvent(allowed=false) disables user input until either
    InputAllowedEvent(allowed=true) or HandlerEndEvent is received.

    Args:
        allowed: User input allowed
    """

    def __init__(self, allowed: bool):
        super().__init__(
            "input_allowed",
            {
                "allowed": allowed,
            },
        )


class DTMFEvent(Event):
    """Event for DTMF input.

    This event is for internal use only. It is used to store DTMF input.
    """

    def __init__(self, digits: str):
        super().__init__("dtmf", {"digits": digits})


def event_to_dict(event: Event) -> dict:
    """Convert an Event object to its dict representation.

    Args:
        event: The Event object to serialize

    Returns:
        Dict representation of the event
    """
    return {
        "name": event.name,
        "data": event.data,
        "timestamp": event.timestamp,
        "turn": event.turn,
        "background": event.background,
        "background_task_name": event.background_task_name,
    }


def event_to_str(event: Event) -> str:
    """Convert an Event object to its JSON string representation.

    Args:
        event: The Event object to serialize

    Returns:
        JSON string representation of the event
    """
    return json.dumps(event_to_dict(event))


def event_from_str(event_str: str) -> Event:
    """Deserialize a JSON string into an Event object.

    This function parses a JSON string and creates the appropriate Event
    subclass based on the event name. Supports dynamic handling for
    metrics namespace events.

    Args:
        event_str: JSON string representation of an event

    Returns:
        An Event object of the appropriate subclass

    Raises:
        ValueError: If the event type is unknown or unsupported
    """
    event: dict = json.loads(event_str)
    name = event.get("name")
    data = event.get("data", {})
    timestamp = event.get("timestamp", datetime.now(timezone.utc).isoformat())
    turn = event.get("turn", 0)
    background = event.get("background", False)
    background_task_name = event.get("background_task_name", None)

    # Dynamic handling for metrics namespace
    if isinstance(name, str) and name.startswith("metrics."):
        try:
            _, metric_type, *metric_name_parts = name.split(".")
            metric_name = ".".join(metric_name_parts) if metric_name_parts else ""
        except Exception:
            metric_type = "unknown"
            metric_name = name
        payload = {k: v for k, v in data.items()}
        return MetricEvent(metric_type, metric_name, payload)

    event_types = {
        "stt_model_switched": lambda: STTModelSwitchedEvent(
            data.get("from_model"),
            data.get("to_model"),
            data.get("warmup_ms", 0),
            data.get("switch_delay_ms", 0),
        ),
        "audio": lambda: AudioEvent(data.get("path")),
        "context": lambda: ContextUpdateEvent(data.get("context")),
        "error": lambda: ErrorEvent(data.get("message")),
        "interrupt": InterruptEvent,
        "log": lambda: LogEvent(data.get("message"), data.get("location")),
        "silence": lambda: SilenceEvent(data.get("duration")),
        "start": StartEvent,
        "stop": lambda: StopEvent(
            closing_speech=data.get("closing_speech"),
            voice=data.get("voice"),
            speed=data.get("speed", 1.0),
            language=data.get("language", "en"),
        ),
        "text_to_speech": lambda: TextToSpeechEvent(
            data.get("text"),
            data.get("voice", "nova"),
            data.get("cache", True),
            data.get("interruptible", None),
            data.get("instructions", ""),
            data.get("speed", 1.0),
            data.get("language", "en"),
            data.get("stream"),
        ),
        "text": lambda: TextEvent(
            data.get("source"), data.get("text"), data.get("language")
        ),
        "timeout": lambda: TimeoutEvent(data.get("count"), data.get("ms_since_input")),
        "collect_payment": lambda: CollectPaymentEvent(data.get("amount")),
        "collect_payment_success": CollectPaymentSuccessEvent,
        "supervisor_request": lambda: SupervisorRequestEvent(data.get("content")),
        "supervisor_response": lambda: SupervisorResponseEvent(data.get("content")),
        "connect_sts": lambda: ConnectSTSEvent(data.get("configuration")),
        "disconnect_sts": DisconnectSTSEvent,
        "update_call": lambda: UpdateCallEvent(data.get("data")),
        "start_recording": lambda: StartRecordingEvent(data.get("status_callback_url")),
        "stop_recording": StopRecordingEvent,
        "stt_update_settings": lambda: STTUpdateSettingsEvent(
            data.get("language"),
            data.get("prompt"),
            data.get("endpointing"),
            data.get("noise_reduction_type"),
            data.get("model"),
        ),
        "turn_end": lambda: TurnEndEvent(data.get("duration")),
        "turn_interrupted": TurnInterruptedEvent,
        "initialize": lambda: InitializeEvent(
            data.get("code"),
            data.get("hash"),
            data.get("is_multifile"),
            data.get("is_debug"),
            data.get("context"),
            data.get("tracing_enabled"),
        ),
        "handler_end": HandlerEndEvent,
        "debug": lambda: DebugEvent(
            data.get("event_name"),
            data.get("event_data"),
            data.get("direction"),
            data.get("context"),
        ),
        "session_end": SessionEndEvent,
        "testing": lambda: TestingEvent(data.get("data")),
        "start_session": lambda: StartSessionEvent(
            data.get("agent_id"),
            data.get("environment"),
            data.get("input_type"),
            data.get("input_parameters"),
            data.get("parameters"),
        ),
        "merge_session": lambda: MergeSessionEvent(data.get("session_id")),
        "transfer_session": lambda: TransferSessionEvent(
            phone_number=data.get("phone_number"),
            agent_id=data.get("agent_id"),
            environment=data.get("environment"),
            data=data.get("data", {}),
            closing_speech=data.get("closing_speech"),
            voice=data.get("voice"),
            speed=data.get("speed", 1.0),
            language=data.get("language", "en"),
        ),
        "transcript_part": lambda: TranscriptPartEvent(
            data.get("role"), data.get("content")
        ),
        "input_allowed": lambda: InputAllowedEvent(data.get("allowed")),
        "dtmf": lambda: DTMFEvent(data.get("digits")),
    }

    if name in event_types:
        e = event_types[name]()
        e.timestamp = timestamp
        e.turn = turn
        e.background = background
        e.background_task_name = background_task_name
        return e

    raise ValueError(f"Unknown event type: {name}")


def format_event(event: Event) -> bytes:
    """Format an Event object as bytes for transmission.

    Converts an Event to its JSON string representation and encodes
    it as UTF-8 bytes with a newline terminator.

    Args:
        event: The Event object to format

    Returns:
        UTF-8 encoded bytes representation of the event
    """
    event_string = event_to_str(event)

    return bytes(f"{event_string}\n", "utf-8")
