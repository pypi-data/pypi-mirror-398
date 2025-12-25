import asyncio
import collections.abc
import logging
import signal

import hypercorn.asyncio


async def serve_http(app, port=8000):
    config = hypercorn.Config()
    config.bind = [f"0.0.0.0:{int(port)}"]
    config.accesslog = logging.getLogger("hypercorn.access")
    config.access_log_format = '[%(s)s] %(m)s %(U)s?%(q)s [%(L)ss] %(b)s "%(h)s"'
    config.errorlog = logging.getLogger("hypercorn.error")

    shutdown_trigger = None
    has_custom_handlers = any(
        signal.getsignal(signum) not in {signal.default_int_handler, signal.SIG_DFL}
        for signum in (signal.SIGINT, signal.SIGTERM)
    )
    if has_custom_handlers:
        # prevent hypercorn from catching `SIGTERM` and `SIGINT` if
        # other signal handlers are already installed elsewhere.
        shutdown_trigger = asyncio.Event().wait

    await hypercorn.asyncio.serve(app, config, shutdown_trigger=shutdown_trigger)


SHUTDOWN_SIGNALS = (signal.SIGINT, signal.SIGTERM)


class _ShutdownError(Exception): ...


async def run_forever(*coros: collections.abc.Coroutine) -> None:
    loop = asyncio.get_running_loop()
    signal_future: asyncio.Future = asyncio.Future()

    def on_signal() -> None:
        signal_future.set_exception(_ShutdownError())

        for signum in SHUTDOWN_SIGNALS:
            loop.remove_signal_handler(signum)

    for signum in SHUTDOWN_SIGNALS:
        loop.add_signal_handler(signum, on_signal)

    async def raise_on_exit(coro: collections.abc.Awaitable) -> None:
        await coro

        raise RuntimeError(f"Coroutine `{coro}` exited unexpectedly")

    try:
        async with asyncio.TaskGroup() as task_group:
            for coro in signal_future, *coros:
                task_group.create_task(raise_on_exit(coro))

    except* _ShutdownError:
        pass
