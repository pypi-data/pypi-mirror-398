import asyncio
import collections.abc
import logging
import signal

from .client import RpcClient
from .models import Options, RpcCall
from .queue_client import QueueClient
from .server import RpcServer
from .workflow import RpcWorkflow

__all__ = ["Options", "Rpc", "RpcCall", "run_forever"]

logger = logging.getLogger(__name__)


class Rpc:
    def __init__(self, service_name: str, connection_string: str) -> None:
        self._connection_string = connection_string
        self._queue_client = QueueClient(service_name, self._connection_string)

        self.client = RpcClient(self._queue_client)
        self.server = RpcServer(self._queue_client)
        self.workflow = RpcWorkflow(self._queue_client)

        self._servers: dict[str, RpcServer] = {
            service_name: self.server,
        }

    async def run(self) -> None:
        if not self._connection_string:
            logger.warning(
                "RPC hasn't been run because `connection_string` is undefined."
                "Pass a non-empty `connection_string` while initializing."
            )
            await asyncio.Future()
            return

        for server in self._servers.values():
            await server.start()

        await self.workflow.start()

        try:
            await asyncio.Future()
        finally:
            await self._queue_client.stop()

    def get_server(self, service_name: str) -> RpcServer:
        server = self._servers.get(service_name)
        if not server:
            self._servers[service_name] = RpcServer(
                self._queue_client,
                service_name=service_name,
            )

        return self._servers[service_name]


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
