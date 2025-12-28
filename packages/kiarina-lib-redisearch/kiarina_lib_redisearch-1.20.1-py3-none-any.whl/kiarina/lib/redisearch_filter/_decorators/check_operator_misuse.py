from functools import wraps
from typing import Any, Callable


def check_operator_misuse(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to check misuse of the equality operator
    """

    @wraps(func)
    def wrapper(instance: Any, *args: Any, **kwargs: Any) -> Any:
        other = kwargs.get("other") if "other" in kwargs else None

        if not other:
            for arg in args:
                if isinstance(arg, type(instance)):
                    other = arg
                    break

        if isinstance(other, type(instance)):
            raise ValueError(
                "The equality operator is overridden when creating a FilterExpression."
                "Use .equals() for equality checks."
            )

        return func(instance, *args, **kwargs)

    return wrapper
