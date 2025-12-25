import asyncio
import functools
import inspect
import logging
import time
from typing import Any, Callable, Literal

import pydantic

from . import errors, metrics, utils
from .models import BaseModel, Request, Response, Result, RpcCall
from .queue_client import QueueClient

logger = logging.getLogger(__name__)


RpcCallPath = tuple[Literal["args"], int] | tuple[Literal["kwargs"], str]


class Context(BaseModel):
    handler_name: str
    rpc_call_path: RpcCallPath
    args: tuple[RpcCall | Any, ...]
    kwargs: dict[str, RpcCall | Any]


class RpcWorkflow:
    def __init__(self, queue_client: QueueClient) -> None:
        self._queue_client = queue_client
        self._queue_name = f"workflow.{self._queue_client.service_name}"

        self._prefetch_count = 1
        self._started = False

        self._handlers: dict[str, tuple[inspect.Signature, Callable]] = {}

    def set_prefetch_count(self, prefetch_count: int) -> None:
        if self._started:
            raise RuntimeError(
                "Prefetch count must be configured before workflow start"
            )

        self._prefetch_count = prefetch_count

    async def start(self) -> None:
        if not self._handlers:
            return

        if self._started:
            raise RuntimeError("Workflow has been already started")

        await self._queue_client.declare_consume_named_queue(
            queue_name=self._queue_name,
            handler=self._on_message,
            prefetch_count=self._prefetch_count,
        )

        logger.info("RPC workflow is consuming messages from `%s`", self._queue_name)
        self._started = True

    def step(
        self,
        handler: Callable | None = None,
        *,
        name: str | None = None,
    ) -> Callable:
        def decorator(handler: Callable) -> Callable:
            handler_name = self._register_handler(handler=handler, name=name)

            @functools.wraps(handler)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await self._resolve_or_call(handler_name, args, kwargs)

            return wrapper

        if handler:
            return decorator(handler)

        return decorator

    def _register_handler(self, *, handler: Callable, name: str | None = None) -> str:
        handler_name = name or f"{handler.__module__}.{handler.__qualname__}"
        if handler_name in self._handlers:
            raise ValueError(f"Handler {handler_name} is already defined")

        utils.assert_handler_is_coroutine(handler)

        signature = inspect.signature(handler)

        handler = pydantic.validate_call(
            validate_return=True,
            config=pydantic.ConfigDict(arbitrary_types_allowed=True),
        )(handler)

        self._handlers[handler_name] = signature, handler

        return handler_name

    async def _resolve_or_call(
        self,
        handler_name: str,
        args: tuple[RpcCall | Any, ...],
        kwargs: dict[str, RpcCall | Any],
        timings: list[tuple[str, float]] | None = None,
    ) -> Any:
        if handler_name not in self._handlers:
            raise errors.UnknownMethodError(handler_name)

        signature, handler = self._handlers[handler_name]
        signature.bind(*args, **kwargs)

        next_unresolved_rpc_call: RpcCall | None = None
        next_unresolved_rpc_call_path: RpcCallPath | None = None

        for arg_index, arg in enumerate(args):
            if isinstance(arg, RpcCall) and not arg.is_done:
                next_unresolved_rpc_call = arg
                next_unresolved_rpc_call_path = ("args", arg_index)
                break

        if next_unresolved_rpc_call is None:
            for arg_key, arg in kwargs.items():
                if isinstance(arg, RpcCall) and not arg.is_done:
                    next_unresolved_rpc_call = arg
                    next_unresolved_rpc_call_path = ("kwargs", arg_key)
                    break

        if next_unresolved_rpc_call is None:
            with metrics.workflow_handler_calls_in_progress.labels(
                handler=handler_name,
            ).track_inprogress():
                elapsed = -time.perf_counter()
                error = ""

                try:
                    result = await handler(*args, **kwargs)
                except Exception:
                    error = "ExecutionError"
                    raise
                finally:
                    elapsed += time.perf_counter()
                    metrics.workflow_handler_call_processed(
                        handler=handler_name,
                        elapsed=elapsed,
                        error=error,
                    )

            return result

        assert next_unresolved_rpc_call
        assert next_unresolved_rpc_call_path

        next_unresolved_rpc_call_arguments = next_unresolved_rpc_call.arguments
        next_unresolved_rpc_call.arguments = {}

        context_bytes = await asyncio.to_thread(
            Context(
                rpc_call_path=next_unresolved_rpc_call_path,
                handler_name=handler_name,
                args=args,
                kwargs=kwargs,
            ).model_dump_msgpack
        )
        if len(context_bytes) > utils.COMPRESS_MIN_SIZE:
            context_bytes, _ = await asyncio.to_thread(
                utils.compress,
                context_bytes,
                encoding="zstd",
            )

        request = Request(
            method_name=next_unresolved_rpc_call.method_name,
            arguments=next_unresolved_rpc_call_arguments,
            context=context_bytes,
            timings=timings or [],
        )
        del context_bytes

        await self._queue_client.send(
            **(await asyncio.to_thread(request.model_dump_message)),
            exchange_name=f"service.{next_unresolved_rpc_call.service_name}",
            routing_key=f"method.{next_unresolved_rpc_call.method_name}",
            reply_to=self._queue_name,
            priority=next_unresolved_rpc_call.options.priority,
            timeout=None,
        )

        metrics.workflow_rpc_calls_sent_count.labels(
            service=next_unresolved_rpc_call.service_name,
            method=next_unresolved_rpc_call.method_name,
            handler=handler_name,
            priority=next_unresolved_rpc_call.options.priority,
        ).inc()

        return ...

    async def _on_message(
        self,
        body: bytes,
        content_type: str,
        message_type: str,
        message_id: str,
        priority: int,
        published_timestamp: float | None = None,
        **_: Any,
    ) -> Any:
        consumed_timestamp = time.time()

        response = await asyncio.to_thread(
            Response.model_validate_message,
            body=body,
            content_type=content_type,
            message_type=message_type,
        )
        if not response.context:
            logger.warning("[MID:%s] Message has empty context", message_id)
            return None

        encoding = utils.get_encoding(response.context)
        if encoding:
            try:
                context_bytes = await asyncio.to_thread(
                    utils.decompress,
                    response.context,
                    encoding=encoding,
                )
            except Exception as error:
                raise errors.BadMessageError(f"Decompression failed: `{error!r}`")
        else:
            context_bytes = response.context

        context = await asyncio.to_thread(
            Context.model_validate_msgpack,
            context_bytes,
        )
        del context_bytes

        arg_type, key = context.rpc_call_path

        if arg_type == "args":
            assert isinstance(key, int)
            rpc_call = context.args[key]
        else:
            assert isinstance(key, str)
            rpc_call = context.kwargs[key]

        rpc_call.result = Result(
            result=response.result,
            error=response.error,
        )

        timings = response.timings
        queued_for = None
        if published_timestamp is not None:
            queued_for = consumed_timestamp - published_timestamp

        timings.append(
            (
                f"queue.consumed.workflow by {self._queue_client.app_id}",
                consumed_timestamp,
            ),
        )

        logger.info(
            "[MID:%s] Resolved %r %s for %s. In queue: %ims, success: %s%s",
            message_id,
            context.rpc_call_path,
            rpc_call,
            context.handler_name,
            (None if queued_for is None else max(queued_for * 1000, 0)),
            response.error is None,
            f", error: {response.error.message}" if response.error else "",
        )

        metrics.workflow_rpc_call_resolved(
            service=rpc_call.service_name,
            method=rpc_call.method_name,
            handler=context.handler_name,
            priority=priority,
            queued_for=queued_for or 0,
            error=response.error,
        )

        return await self._resolve_or_call(
            context.handler_name,
            context.args,
            context.kwargs,
            timings=timings,
        )
