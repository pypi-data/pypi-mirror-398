from typing import Any, Callable

from warpzone.function.processors.dependencies import DependencyProcessor
from warpzone.function.processors.outputs import OutputProcessor
from warpzone.function.processors.triggers import TriggerProcessor

SingleArgumentCallable = Callable[[Any], Any]


def get_function_type(
    trigger: TriggerProcessor,
    output: OutputProcessor,
    dependencies: list[DependencyProcessor],
) -> SingleArgumentCallable:
    # Disable annotation because pytype handles a list of arbitrary fields as
    # ambiguous and gives an error
    return Callable[
        [trigger.arg_type] + [dep.return_type for dep in dependencies],
        output.return_type,
    ]  # pytype: disable=invalid-annotation
