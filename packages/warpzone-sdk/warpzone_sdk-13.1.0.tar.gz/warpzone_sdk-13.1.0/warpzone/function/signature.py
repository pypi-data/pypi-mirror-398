import asyncio
from typing import Callable

import azure.functions as func

from warpzone.function.processors import outputs, triggers


def redefine_signature(
    f: Callable,
    trigger: triggers.TriggerProcessor,
    output: outputs.OutputProcessor,
) -> Callable:
    """Wrap Azure function to have correct
    argument name and type, and return type.
    This is required to make sure it is
    executed correctly in a Function App.

    Args:
        f (Callable): Azure function to be wrapped
        trigger (triggers.TriggerProcessor): Trigger processor
        output (outputs.OutputProcessor): Output processor

    Returns:
        Callable: Azure function with
            - argument
                name: "<trigger.binding_name>"
                annotation: "<trigger.arg_type>"
                description: argument of the original function
            - argument
                name: "context"
                annotation: "azure.functions.Context"
                description: Azure function context
            - return value
                annotation: "<output.return_type>"
                description: return value of original function
    """
    local_variables = {
        "f": f,
        "arg_type": trigger.arg_type,
        "return_type": output.return_type,
        "func": func,
    }
    # NOTE: Changing the names and annotations
    # of a functions is a difficult task.
    # We have chosen to use dynamically execution
    # for creating a a redefined function,
    # as this is the most straight-forward
    # way to do it. A new proposal is welcome,
    # as using `exec` can be seen as bad practice.
    if asyncio.iscoroutinefunction(f):
        exec(
            f"""async def new_f(
                {trigger.binding_name}: arg_type,
                context: func.Context
            ) -> return_type:
            return await f({trigger.binding_name}, context)
        """,
            local_variables,
        )
    else:
        exec(
            f"""def new_f(
                {trigger.binding_name}: arg_type,
                context: func.Context
            ) -> return_type:
            return f({trigger.binding_name}, context)
        """,
            local_variables,
        )

    return local_variables["new_f"]
