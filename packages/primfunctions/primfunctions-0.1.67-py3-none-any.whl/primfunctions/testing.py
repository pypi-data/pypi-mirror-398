from typing import Dict, cast
import random


class TestData:
    """
    A test data object is used to track the data for a test.
    """

    def __init__(self, data: dict = {}):
        self.current_iterations = data.get("current_iterations", 0)
        self.current_confidence = data.get("current_confidence", 0)

    def __dict__(self):
        return {
            "current_iterations": self.current_iterations,
            "current_confidence": self.current_confidence,
        }


class Test:
    """
    A test is used to randomly generate (with probabilities) a value based on the options.
    """

    def __init__(
        self,
        name: str,
        options: dict,
        description: str = "",
        stop: dict = {},
        runTest: bool = True,
        value: any = None,
    ):
        """
        A test is used to randomly generate (with probabilities) a value based on the options.
        name: the name of the test
        options: a dictionary of options with their probabilities
        description: a description of the test
        stop: a dictionary of stop conditions (iterations, confidence).
        If stop is not provided, the test will run indefinitely.
        If one stop condition is provided, the test will run until the stop condition is met.
        If two stop conditions are provided, the test will run until any (stop_on=1) or both (stop_on=2) stop conditions are met.
        If the test reaches a stop condition, the test will return the default value.
        As soon as the test reaches a stop condition, all emails addresses in the notify list will be notified.
        """
        self.name = name
        self.options = options
        self.description = description
        self.value = value
        self.stop = {}

        # Add stop conditions
        self.add_stop(stop, runTest)

    def add_stop(self, stop: dict, runTest: bool):
        """
        Add stop conditions to the test.
        """
        if not stop:
            # No stop conditions, so no need to add anything
            return

        # Add default value (required)
        if not stop.get("default", None):
            raise ValueError("Stop must have a default value")
        self.stop["default"] = stop["default"]

        # Add max iterations, if provided
        if iterations := stop.get("iterations", None):
            if not isinstance(iterations, int) or iterations < 0:
                raise ValueError("Iterations must be a positive integer")
            self.stop["max_iterations"] = iterations

        # Add max confidence, if provided
        if confidence := stop.get("confidence", None):
            if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
                raise ValueError("Confidence must be an integer between 0 and 100")
            self.stop["max_confidence"] = confidence

            # Add target outcome (required when confidence is provided)
            if not (targetOutcome := stop.get("target_outcome", None)):
                raise ValueError(
                    "target_outcome is required when confidence is provided"
                )
            self.stop["target_outcome"] = targetOutcome

        # Add stop on (1 for either, 2 for both)
        stop_on = stop.get("stop_on", 1)
        if not isinstance(stop_on, int) or stop_on not in [1, 2]:
            raise ValueError("Stop on must be either 1 or 2")
        self.stop["stop_on"] = stop_on

        # Add notify list (optional)
        if stop.get("notify", None) and not isinstance(stop["notify"], list):
            raise ValueError("Notify must be a list of email addresses")
        self.stop["notify"] = stop["notify"]

        self.stop["running"] = runTest

        if not runTest:
            self.value = self.stop["default"]

    def get(self):
        """
        Run the test and return the value.
        """
        if self.value is None:
            # Use random.choices for weighted selection
            keys = list(self.options.keys())
            weights = list(self.options.values())
            self.value = random.choices(keys, weights=weights, k=1)[0]
        return self.value

    def __dict__(self):
        return {
            "name": self.name,
            "description": self.description,
            "options": self.options,
            "value": self.value,
            "stop": self.stop,
        }


outcome_types = {
    "boolean": {"python_type": bool, "default": False},
    "integer": {"python_type": int, "default": 0},
    "float": {"python_type": float, "default": 0.0},
    "string": {"python_type": str, "default": ""},
}


class Outcome:
    """
    An outcome is used to track various metrics throughout a session.
    """

    def __init__(self, name: str, type: str, description: str = "", value: any = None):
        """
        An outcome is used to track various metrics throughout a session.
        name: the name of the outcome
        type: the type of the outcome (boolean, integer, float, string)
        description: a description of the outcome
        """
        type = type.lower()
        if type not in outcome_types:
            raise ValueError("Invalid outcome type: " + type)
        self.name = name
        self.type = type
        self.description = description
        self.python_type = outcome_types[type]["python_type"]
        self.default = outcome_types[type]["default"]
        self.value = value if value is not None else self.default

    def get(self):
        return self.value

    def set(self, value):
        try:
            value = cast(self.python_type, value)
        except:
            raise TypeError("Value must be of type " + self.type)
        finally:
            prev = self.value
            self.value = value
            return prev

    def trigger(self):
        prev = self.value
        match self.type:
            case "boolean":
                self.value = True
            case "integer":
                self.value += 1
            case _:
                raise ValueError

        return prev

    def reset(self):
        prev = self.value
        self.value = self.default
        return prev

    def __dict__(self):
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "value": self.value,
        }


class Testing:
    """
    A testing object is used to track various tests and outcomes throughout a session.
    """

    def __init__(
        self,
        tests: Dict[str, Test] = {},
        outcomes: Dict[str, Outcome] = {},
        runTest: Dict[str, bool] = {},
        metadata: Dict[str, any] = {},
    ):
        self.tests: Dict[str, Test] = tests
        self.outcomes: Dict[str, Outcome] = outcomes
        self.runTest: Dict[str, bool] = runTest
        self.metadata: Dict[str, any] = metadata

    def add_test(
        self, name: str, options: dict, description: str = "", stop: dict = {}
    ):
        """
        Add a test to the testing object.
        """
        if name not in self.tests:
            self.tests[name] = Test(
                name, options, description, stop, self.runTest.get(name, True)
            )
        return self.tests[name].get()

    def get_test(self, name: str) -> Test:
        """
        Get a test by name.
        """
        if name not in self.tests:
            raise ValueError("Test not found")
        return self.tests[name].get()

    def add_tests(self, tests: list[dict]):
        """
        Add a list of tests to the testing object.
        """
        for test in tests:
            if (name := test.get("name", None)) and (
                options := test.get("options", None)
            ):
                self.add_test(
                    name, options, test.get("description", ""), test.get("stop", {})
                )
            else:
                raise ValueError("Test must have a name and options")

    def add_outcome(self, name: str, type: str, description: str = ""):
        """
        Add an outcome to the testing object.
        """
        if name not in self.outcomes:
            self.outcomes[name] = Outcome(name, type, description)
        return self.outcomes[name].get()

    def get_outcome(self, name: str) -> Outcome:
        """
        Get an outcome by name.
        """
        if name not in self.outcomes:
            raise ValueError("Outcome not found")
        return self.outcomes[name].get()

    def set_outcome(self, name: str, value: any):
        """
        Set an outcome by name.
        """
        if name not in self.outcomes:
            raise ValueError("Outcome not found")
        return self.outcomes[name].set(value)

    def trigger_outcome(self, name: str):
        """
        Trigger an outcome by name.
        """
        if name not in self.outcomes:
            raise ValueError("Outcome not found")
        return self.outcomes[name].trigger()

    def reset_outcome(self, name: str):
        """
        Reset an outcome by name.
        """
        if name not in self.outcomes:
            raise ValueError("Outcome not found")
        return self.outcomes[name].reset()

    def add_outcomes(self, outcomes: list[dict]):
        """
        Add a list of outcomes to the testing object.
        """
        for outcome in outcomes:
            if (name := outcome.get("name", None)) and (
                type := outcome.get("type", None)
            ):
                self.add_outcome(name, type, outcome.get("description", ""))
            else:
                raise ValueError("Outcome must have a name and type")

    def set_metadata(self, key: str, value: any):
        """
        Set a metadata value.
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: any = None):
        """
        Get a metadata value.
        """
        return self.metadata.get(key, default)

    def __dict__(self):
        return {
            "tests": {name: test.__dict__() for name, test in self.tests.items()},
            "outcomes": {
                name: outcome.__dict__() for name, outcome in self.outcomes.items()
            },
            "runTest": self.runTest,
            "metadata": self.metadata,
        }
