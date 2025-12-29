import asyncio
from collections.abc import Coroutine
from subprocess import PIPE
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterable

type Coro[T] = Coroutine[Any, Any, T]


async def exec_command(command: str) -> tuple[bool, tuple[bytes, bytes]]:
    proc = await asyncio.create_subprocess_shell(command, stdout=PIPE, stderr=PIPE)
    output_streams = await proc.communicate()
    return proc.returncode == 0, output_streams


async def concurrent_iter[T](coroutines: Iterable[Coro[T]]) -> AsyncIterator[T]:
    tasks: list[asyncio.Task[T]] = [asyncio.create_task(coro) for coro in coroutines]
    for task in tasks:
        yield await task


async def concurrent_list[T](coroutines: Iterable[Coro[T]]) -> list[T]:
    return [item async for item in concurrent_iter(coroutines)]


async def concurrent_call[A, T](
    async_func: Callable[[A], Coro[T]], args_list: list[A]
) -> list[T]:
    return await concurrent_list(async_func(args) for args in args_list)
