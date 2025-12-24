import asyncio
import json
import uuid

from typing import List, Dict, Any, Callable, Coroutine

from .configuration import Configuration, LLMProvider
from .events import Event, ErrorEvent
from .testing import Testing, Test, Outcome
from .utils.errors import format_error_with_filtered_traceback
from .completions.messages import (
    ConversationHistory,
    ConversationHistoryMessage,
    serialize_conversation,
    deserialize_conversation,
)


class Context:
    def __init__(
        self,
        agent_id: str = "",
        environment: str = "",
        session_id: str = "",
        configuration: Configuration = Configuration(),
        data: dict = {},
        variables: Dict[str, float] = {},
        on_event: Callable[[Event], None] = lambda: None,
        on_debug_event: Callable[[Event, str, dict], None] = lambda: None,
    ):
        self.agent_id = agent_id
        self.environment = environment
        self.session_id = session_id
        self.configuration = configuration
        self.data = data
        self.variables = variables
        self.history = []
        self._conversation_history_json: List[dict] = []  # Store as JSON internally
        self.testing = Testing(runTest=json.loads(self.data.get("runTest", "{}")))
        self.function_id = self.data.get("functionId", "")
        self.on_event = on_event
        self.on_debug_event = on_debug_event
        self.tasks: Dict[str, asyncio.Task] = {}

        if "runTest" in self.data:
            del self.data["runTest"]  # Remove runTest from data
        if "functionId" in self.data:
            del self.data["functionId"]  # Remove functionId from data

    def add_test(self, name, options, description="", stop={}):
        """
        Add a test to the context.

        Args:
            name: The name of the test.
            options: The options for the test as option:weight pairs.
            description: The description of the test.
            stop: The stop conditions for the test as
                iterations:integer greater than 0,
                confidence:integer between 0 and 100,
                target_outcome:string name of outcome,
                stop_on:1 (either) or 2 (both),
                default:value (required),
                notify:list of email addresses (optional).

        Returns:
            The value of the test.
        """
        return self.testing.add_test(name, options, description, stop)

    def get_test(self, name):
        """
        Get the value of a test.

        Args:
            name: The name of the test.

        Returns:
            The value of the test.
        """
        return self.testing.get_test(name)

    def add_tests(self, tests: list[dict]):
        """
        Add a list of tests to the context.

        Args:
            tests: A list of tests as dictionaries with name, options, description (optional), and stop (optional).
        """
        self.testing.add_tests(tests)

    def add_outcome(self, name, type, description=""):
        """
        Add an outcome to the context.

        Args:
            name: The name of the outcome.
            type: The type of the outcome as boolean, integer, float, or string.
            description: The description of the outcome.

        Returns:
            The value of the outcome.
        """
        self.testing.add_outcome(name, type, description)

    def get_outcome(self, name):
        """
        Get the value of an outcome.

        Args:
            name: The name of the outcome.

        Returns:
            The value of the outcome.
        """
        return self.testing.get_outcome(name)

    def set_outcome(self, name, value):
        """
        Set the value of an outcome.

        Args:
            name: The name of the outcome.
            value: The value of the outcome.
            type: The type of the outcome (optional, in case the outcome is not yet defined).
            description: The description of the outcome (optional, in case the outcome is not yet defined).

        Returns:
            The previous value of the outcome (None if the outcome was not yet defined).
        """
        return self.testing.set_outcome(name, value)

    def trigger_outcome(self, name):
        """
        Trigger an outcome.

        Args:
            name: The name of the outcome (must be a boolean or integer).
            type: The type of the outcome (optional, in case the outcome is not yet defined).
            description: The description of the outcome (optional, in case the outcome is not yet defined).

        Returns:
            The previous value of the outcome (None if the outcome was not yet defined).
        """
        return self.testing.trigger_outcome(name)

    def reset_outcome(self, name):
        """
        Reset an outcome.

        Args:
            name: The name of the outcome.
            type: The type of the outcome (optional, in case the outcome is not yet defined).
            description: The description of the outcome (optional, in case the outcome is not yet defined).

        Returns:
            The previous value of the outcome (None if the outcome was not yet defined).
        """
        return self.testing.reset_outcome(name)

    def add_outcomes(self, outcomes: list[dict]):
        """
        Add a list of outcomes to the context.

        Args:
            outcomes: A list of outcomes as dictionaries with name, type, and description (optional).
        """
        self.testing.add_outcomes(outcomes)

    def set_testing_metadata(self, key: str, value: any):
        """
        Set a metadata value in testing.

        Args:
            key: The key of the metadata.
            value: The value of the metadata.
        """
        self.testing.set_metadata(key, value)

    def get_testing_metadata(self, key: str, default: any = None):
        """
        Get a metadata value from testing.

        Args:
            key: The key of the metadata.
            default: The default value if the key is not found.
        """
        return self.testing.get_metadata(key, default)

    def serialize(self) -> dict:
        """
        Serialize the context.

        Returns:
            The serialized context.
        """
        return {
            "agent_id": self.agent_id,
            "environment": self.environment,
            "session_id": self.session_id,
            "function_id": self.function_id,
            "configuration": self.configuration.__dict__(),
            "data": self.data,
            "history": self.history,
            "conversation_history": self._conversation_history_json,
            "variables": self.variables,
            "testing": self.testing.__dict__(),
        }

    def deserialize(self, state: dict):
        """
        Deserialize the context.

        Args:
            state: The serialized context.
        """
        self.agent_id = state.get("agent_id", self.agent_id)
        self.environment = state.get("environment", self.environment)
        self.session_id = state.get("session_id", self.session_id)
        self.function_id = state.get("function_id", self.function_id)
        self.configuration = Configuration(
            **state.get("configuration", self.configuration.__dict__())
        )
        self.data = state.get("data", self.data)
        self.history = state.get("history", self.history)
        self._conversation_history_json = state.get("conversation_history", [])
        self.variables = state.get("variables", self.variables)

        testing_state: dict = state.get("testing", {})
        tests_dict: Dict[str, dict] = testing_state.get("tests", {})
        outcomes_dict: Dict[str, dict] = testing_state.get("outcomes", {})
        runTest: Dict[str, bool] = testing_state.get("runTest", {})
        metadata: Dict[str, any] = testing_state.get("metadata", {})

        tests = {}
        for name, test_data in tests_dict.items():
            # Test expects: name, options, description, stop, runTest
            tests[name] = Test(
                name=test_data.get("name", name),
                options=test_data.get("options", {}),
                description=test_data.get("description", ""),
                stop=test_data.get("stop", {}),
                runTest=runTest.get(name, True),
                value=test_data.get("value", None),
            )

        outcomes = {}
        for name, outcome_data in outcomes_dict.items():
            # Outcome expects: name, type, description
            outcomes[name] = Outcome(
                name=outcome_data.get("name", name),
                type=outcome_data.get("type", "boolean"),
                description=outcome_data.get("description", ""),
                value=outcome_data.get("value", None),
            )

        self.testing = Testing(tests=tests, outcomes=outcomes, runTest=runTest, metadata=metadata)

    def set_data(self, key: str, value: Any):
        """
        Set the value of a data key.

        Args:
            key: The key of the data.
            value: The value of the data.
        """
        self.data[key] = value

    def get_data(self, key: str, default: Any = None):
        """
        Get the value of a data key.

        Args:
            key: The key of the data.
            default: The default value if the key is not found.
        """
        return self.data.get(key, default)

    # Backward compatible methods - these work with OpenAI format internally
    def add_system_message(self, message: str):
        """
        Add system message. For Gemini, this will be converted when getting formatted history.

        Args:
            message: The message to add.
        """
        self.history.append({"role": "system", "content": message})

    def add_assistant_message(self, message: str):
        """
        Add assistant message. For Gemini, this will be converted to 'model' role when getting formatted history.

        Args:
            message: The message to add.
        """
        self.history.append({"role": "assistant", "content": message})

    def add_user_message(self, message: str):
        """
        Add user message. Works the same for both OpenAI and Gemini.

        Args:
            message: The message to add.
        """
        self.history.append({"role": "user", "content": message})

    def add_tool_message(self, tool_name: str, result: str, tool_call_id: str):
        """
        Add a tool result message to the history.

        This is useful for models (like OpenAI GPT) that support tool call messages,
        where the assistant first emits a tool call and then receives a tool result
        as a `role="tool"` message.

        Both tool name and tool_call_id are required for proper attribution.

        Args:
            tool_name: Name of the tool/function that was executed (must be non-empty).
            result: Serialized result returned by the tool (often JSON or text).
            tool_call_id: tool_call_id from the preceding assistant tool call message (must be non-empty).
        """
        if not tool_name:
            raise ValueError("tool_name is required for tool messages")
        if not tool_call_id:
            raise ValueError("tool_call_id is required for tool messages")

        message = {
            "role": "tool",
            "name": tool_name,
            "content": result,
            "tool_call_id": tool_call_id,
        }
        self.history.append(message)

    # New generic methods for flexibility
    def add_message(self, role: str, content: str):
        """
        Generic method to add any message with specified role.

        Args:
            role: The role of the message.
            content: The content of the message.
        """
        self.history.append({"role": role, "content": content})

    def get_history(self, turns: int = 0) -> List[Dict[str, str]]:
        """
        Get history in original OpenAI format for backward compatibility.

        Args:
            turns: The number of turns to get.
        """
        if turns == 0:
            return self.history
        return self.history[-(turns * 2) :]

    def get_history_message(self, turns: int = 0) -> List[Dict[str, str]]:
        """
        Get history formatted for the current model provider.

        Args:
            turns: The number of turns to get.
        """
        history = self.get_history(turns)

        if self.configuration.llm_provider == LLMProvider.OPENAI:
            return history
        elif self.configuration.llm_provider == LLMProvider.GEMINI:
            return self._convert_to_gemini_format(history)
        else:
            return history

    # New utility methods working with completions client
    def get_conversation_history(self) -> ConversationHistory:
        """Get conversation history from context (deserializes from JSON, returns new objects)."""
        return deserialize_conversation(self._conversation_history_json)

    def add_conversation_message(self, message: ConversationHistoryMessage):
        """Add a message to the conversation history."""
        # Serialize the message and add to JSON storage
        self._conversation_history_json.append(message.serialize())

    def set_conversation_history(self, history: ConversationHistory):
        """Set the entire conversation history, replacing any existing history."""
        self._conversation_history_json = serialize_conversation(history)

    def _convert_to_gemini_format(
        self, history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Convert OpenAI format to Gemini format.

        Args:
            history: The history to convert.
        """
        converted = []
        system_messages = []

        for message in history:
            role = message["role"]
            content = message["content"]

            if role == "system":
                # Collect system messages to prepend to first user message
                system_messages.append(content)
            elif role == "assistant":
                # Convert assistant to model for Gemini
                converted.append({"role": "model", "content": content})
            elif role == "user":
                # If we have accumulated system messages, prepend them to this user message
                if system_messages:
                    system_context = "\n".join(system_messages)
                    content = f"System: {system_context}\n\nUser: {content}"
                    system_messages = []  # Clear after using
                converted.append({"role": "user", "content": content})
            else:
                # Unknown role, keep as is
                converted.append(message)

        # If there are remaining system messages at the end, add them as a user message
        if system_messages:
            system_content = "\n".join(system_messages)
            converted.append({"role": "user", "content": f"System: {system_content}"})

        return converted

    def set_llm_provider(self, provider: LLMProvider):
        """
        Change the llm provider for this context.

        Args:
            provider: The llm provider to set.
        """
        self.configuration.llm_provider = provider

    def get_llm_provider(self) -> LLMProvider:
        """
        Get the current llm provider.

        Returns:
            The current llm provider.
        """
        return self.configuration.llm_provider

    def _send_event_from_background(self, event: Event, name: str):
        assert isinstance(event, Event), f"event is not of type Event: {type(event)}"

        # Mark the event as background
        event.background = True
        event.background_task_name = name

        # Send the event and a debug event
        self.on_event(event)
        self.on_debug_event(event, "output", self.serialize())

    async def _wrap_handler(self, handler: Coroutine, name: str):
        try:
            # Check if the handler is an async generator meaning it will yield output events.
            # If so, iterate over it directly and send the output events back over the WebSocket.
            # Otherwise, just await the handler because there will not be any output events.
            if hasattr(handler, "__aiter__"):
                async for output_event in handler:
                    self._send_event_from_background(output_event, name)
            else:
                await handler
        except Exception as e:
            error_details = format_error_with_filtered_traceback(e)
            self._send_event_from_background(ErrorEvent(error_details), name)

    def create_task(
        self,
        handler: Coroutine,
        name: str = None,
        interruptible: bool = False,
        timeout: int = 30,
    ):
        if name in self.tasks:
            self.cancel_task(name)

        if not name:
            name = str(uuid.uuid4())

        task = asyncio.create_task(self._wrap_handler(handler, name))

        self.tasks[name] = {
            "task": task,
            "timeout_task": asyncio.create_task(
                asyncio.wait_for(task, timeout=timeout)
            ),
            "interruptible": interruptible,
            "timeout": timeout,
        }

        return self.tasks[name]

    def cancel_task(self, name: str):
        if name in self.tasks:
            # Cancel the main task if it is not done
            if "task" in self.tasks[name] and not self.tasks[name]["task"].done():
                self.tasks[name]["task"].cancel()

            # Cancel the timeout task if it is not done
            if (
                "timeout_task" in self.tasks[name]
                and not self.tasks[name]["timeout_task"].done()
            ):
                self.tasks[name]["timeout_task"].cancel()

            del self.tasks[name]

    def cancel_interruptible_tasks(self):
        # Avoid RuntimeError by iterating over a static list of keys
        names_to_cancel = [
            name
            for name, task in self.tasks.items()
            if task.get("interruptible", False)
        ]
        for name in names_to_cancel:
            self.cancel_task(name)

    def cancel_all_tasks(self):
        # Avoid RuntimeError by iterating over a static list of keys
        names_to_cancel = list(self.tasks.keys())
        for name in names_to_cancel:
            self.cancel_task(name)

    def has_unfinished_tasks(self):
        for task_info in self.tasks.values():
            task: asyncio.Task = task_info.get("task")
            if task and not task.done():
                return True

        return False

    async def wait_for_all_tasks(self):
        # Collect all tasks that have not finished.
        tasks_to_wait = []
        for task_info in self.tasks.values():
            task: asyncio.Task = task_info.get("task")
            if task and not task.done():
                tasks_to_wait.append(task)

        async def exhaust_async_generator(gen):
            try:
                async for _ in gen:
                    pass
            except Exception:
                pass

        # Handle both regular tasks and async generators.
        coros_to_wait = []
        for t in tasks_to_wait:
            # If the task is an async generator, exhaust it
            if hasattr(t, "__aiter__") and hasattr(t, "__anext__"):
                coros_to_wait.append(exhaust_async_generator(t))
            else:
                coros_to_wait.append(t)

        # Wait for all tasks to complete.
        if coros_to_wait:
            await asyncio.gather(*coros_to_wait, return_exceptions=True)
