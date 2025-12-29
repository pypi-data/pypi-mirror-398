from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger


class FatalError(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(" ".join(str(a) for a in ["💀", *args]))


def killed_by_errors[**P, T](
    *errors: type[Exception], logger: Logger = None, unknown_message: str = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except tuple(errors or []) as exc:
                raise FatalError(str(exc)) from exc
            except Exception as exc:
                if unknown_message:
                    raise FatalError(unknown_message) from exc
                if logger:
                    logger.exception("Killed by error")
                raise

        return wrapper

    return decorator
