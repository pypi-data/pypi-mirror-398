import anyio
from anyio.abc import BlockingPortal
from typing import Awaitable, Callable, ParamSpec, TypeVar

P = ParamSpec('P')
R = TypeVar('R')

class _DefaultPortalManager:
    """Lazily manages a process-wide AnyIO BlockingPortal.

    The portal runs an event loop in a background thread started via
    anyio.from_thread.start_blocking_portal(). It is created on first access and stopped
    automatically at interpreter shutdown.
    """
    def __init__(self) -> None:
        """Initialize the default portal manager."""
    def get(self) -> BlockingPortal:
        """Return the shared BlockingPortal, creating it if necessary.

        This method is thread-safe: concurrent callers will see the same portal.

        Returns:
            BlockingPortal: The shared default portal.
        """

def get_default_portal() -> BlockingPortal:
    """Return the shared default BlockingPortal.

    Returns:
        BlockingPortal: A process-wide portal running on a background thread.
    """
def asyncify(func: Callable[P, R], *, cancellable: bool = False, limiter: anyio.CapacityLimiter | None = None) -> Callable[P, Awaitable[R]]:
    """Wrap a sync function into an awaitable callable using a worker thread.

    Args:
        func (Callable[P, R]): Synchronous function to wrap.
        cancellable (bool, optional): If True, allow cancellation of the awaiter while running in a
            worker thread. Defaults to False.
        limiter (anyio.CapacityLimiter | None, optional): Capacity limiter to throttle concurrent
            thread usage. Defaults to None.

    Returns:
        Callable[P, Awaitable[R]]: An async function that when awaited will execute `func` in a
        worker thread and return its result.

    Usage:
        ```python
        async def handler() -> int:
            wrapped = asyncify(blocking_func)
            return await wrapped(1, 2)
        ```
    """
def syncify(async_func: Callable[P, Awaitable[R]], *, portal: BlockingPortal | None = None) -> Callable[P, R]:
    """Wrap an async function to be callable from synchronous code.

    Lifecycle and portals:
    1. This helper uses an already running AnyIO `BlockingPortal` to execute the coroutine.
    2. If `portal` is not provided, a process-wide shared portal is used. Its lifecycle is
      managed internally: it is created lazily on first use and shut down automatically at process exit.
    3. If you provide a `portal`, you are expected to manage its lifecycle, typically with a
      context manager. This is recommended when making many calls in a bounded scope since it
      avoids per-call startup costs while allowing deterministic teardown.

    Args:
        async_func (Callable[P, Awaitable[R]]): Asynchronous function to wrap.
        portal (BlockingPortal | None, optional): Portal to use for calling the async function
            from sync code. Defaults to None, in which case a shared default portal is used.

    Returns:
        Callable[P, R]: A synchronous function that runs the coroutine and returns its result.

    Usage:
        ```python
        # Use the default shared portal (most convenient)
        def do_work(x: int) -> int:
            sync_call = syncify(async_func)
            return sync_call(x)
        ```

        ```python
        # Reuse a scoped portal for multiple calls (deterministic lifecycle)
        from anyio.from_thread import start_blocking_portal

        with start_blocking_portal() as portal:
            sync_call = syncify(async_func, portal=portal)
            a = sync_call(1)
            b = sync_call(2)
        ```

    Notes:
        Creating a brand-new portal per call is discouraged due to the overhead of spinning up
        and tearing down a background event loop/thread. Prefer the shared portal or a scoped
        portal reused for a batch of calls.
    """
