from typing import Callable, Optional

import typeguard

from warpzone.function import monitor, process, signature, types
from warpzone.function.processors.dependencies import DependencyProcessor
from warpzone.function.processors.outputs import OutputProcessor
from warpzone.function.processors.triggers import TriggerProcessor
from warpzone.function.types import SingleArgumentCallable


def functionize(
    f: SingleArgumentCallable,
    trigger: TriggerProcessor,
    output: OutputProcessor,
    dependencies: Optional[list[DependencyProcessor]] = None,
) -> Callable:
    """Wrap function as an Azure function.

    Args:
        f (SingleArgumentCallable): Function with
            - argument of type specified in trigger processor
            - return value of type specified in output processor
        trigger (TriggerProcessor): Trigger processor
        output (OutputProcessor): Output processor
        dependencies (list[DependencyProcessor], optional): Dependency processors.
            Defaults to None.

    Returns:
        Callable: Azure function with
            - argument
                name: "<trigger.binding_name>"
                annotation: "<trigger.arg_type>"
                description: pre-argument of the original function
            - argument
                name: "context"
                annotation: "azure.functions.Context"
                description: Azure function context
            - return value
                annotation: "<output.return_type>"
                description: post-return value of the original function
    """
    if not dependencies:
        dependencies = list()

    # check types
    typeguard.check_type(trigger, TriggerProcessor)
    typeguard.check_type(output, OutputProcessor)
    typeguard.check_type(dependencies, list[DependencyProcessor])
    function_type = types.get_function_type(trigger, output, dependencies)
    typeguard.check_type(f, function_type)

    main = process.pre_and_post_process(f, trigger, output, dependencies)

    main = monitor.monitor(main)
    main = signature.redefine_signature(main, trigger, output)
    return main
