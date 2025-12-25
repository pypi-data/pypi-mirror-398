import asyncio
from typing import Callable

from warpzone.function.processors.dependencies import DependencyProcessor
from warpzone.function.processors.outputs import OutputProcessor
from warpzone.function.processors.triggers import TriggerProcessor
from warpzone.function.types import SingleArgumentCallable


def pre_and_post_process(
    f: Callable,
    trigger: TriggerProcessor,
    output: OutputProcessor,
    dependencies: list[DependencyProcessor],
) -> SingleArgumentCallable:
    """Wrap function as an Azure function with
    pre- and post processing. The wrapped function
    is the function composition

        x -> y:

        z  = trigger.process(x)
        w0 = dep0.process(z), w1 = dep1.process(z), ...
        v  = f(z, w0, w1)
        y  = output.process(v)

    Args:
        f (Callable): Function with
            - 1st argument of type specified in trigger processor
            - 2nd...nth arguments of type specified in input processors
            - return value of type specified in output processor
        trigger (TriggerProcessor): Trigger processor
        output (OutputProcessor): Output processor
        dependencies (list[DependencyProcessor]): Dependency processors

    Returns:
        Callable: Azure function with
            - argument "arg":   pre-argument of the original function
            - return value:     post-return value of the original function
    """

    async def wrapper_async(arg):
        processed_arg = trigger._process(arg)
        initialized_deps = [dep.initialize(processed_arg) for dep in dependencies]
        result = await f(processed_arg, *initialized_deps)
        processed_result = output._process(result)
        for dep, initialized_dep in zip(dependencies, initialized_deps):
            dep.finalize(initialized_dep)
        return processed_result

    def wrapper(arg):
        processed_arg = trigger._process(arg)
        initialized_deps = [dep.initialize(processed_arg) for dep in dependencies]
        result = f(processed_arg, *initialized_deps)
        processed_result = output._process(result)
        for dep, initialized_dep in zip(dependencies, initialized_deps):
            dep.finalize(initialized_dep)
        return processed_result

    if asyncio.iscoroutinefunction(f):
        return wrapper_async
    else:
        return wrapper
