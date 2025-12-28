from typing import Protocol, Any, Callable, TypeVar, cast


class FlopFunc(Protocol):
    flops: int

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


F = TypeVar("F", bound=Callable[..., Any])


def attach_flops(func: F, flops: int) -> FlopFunc:
    setattr(func, "flops", flops)
    return cast(FlopFunc, func)
