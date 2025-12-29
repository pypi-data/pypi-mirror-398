from collections.abc import Callable
from copy import copy
from typing import Generic, TypeVar

R = TypeVar("R")


class FnWithKwargs(Generic[R]):
    fn: Callable[..., R]
    args: tuple | None
    kwargs: dict[str] | None

    def __init__(
        self,
        fn: Callable[..., R],
        args: tuple | None = None,
        kwargs: dict[str] | None = None,
    ) -> None:
        self.fn = fn

        if kwargs is None:
            kwargs = {}

        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs) -> R:
        call_kwargs = copy(self.kwargs)
        call_kwargs.update(kwargs)

        if self.args is not None:
            args = self.args

        return self.fn(*args, **call_kwargs)

    def update(self, **kwargs) -> None:
        self.kwargs.update(kwargs)
