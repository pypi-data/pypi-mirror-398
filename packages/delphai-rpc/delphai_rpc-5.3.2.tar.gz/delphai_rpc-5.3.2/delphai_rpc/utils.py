import asyncio
import collections
import contextlib
import contextvars
import dataclasses
import functools
import inspect
import logging
import os
import uuid
import zlib
from typing import Any, Callable, TypeVar, cast

import msgpack
import zstandard
from typing_extensions import ParamSpec

logger = logging.getLogger(__name__)


def assert_handler_is_coroutine(handler: Callable) -> None:
    if not inspect.iscoroutinefunction(handler):
        raise TypeError(f"{handler!r} must be coroutine functions")


def assert_handler_kwargs_only(handler: Callable) -> None:
    positional_only = []
    positional_or_keyword = []

    for parameter_name, parameter in inspect.signature(handler).parameters.items():
        if parameter.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            positional_or_keyword.append(parameter_name)

        elif parameter.kind in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.VAR_POSITIONAL,
        }:
            positional_only.append(parameter_name)

    if positional_only:
        raise TypeError(
            f"{handler!r} has positional-only parameters {positional_only} that are not supported"
        )

    if positional_or_keyword:
        logger.warning(
            "%s has positional parameters %s, only keyword parameters are supported",
            handler,
            positional_or_keyword,
        )


_timeout_contextvar: contextvars.ContextVar[asyncio.Timeout | None] = (
    contextvars.ContextVar("_timeout_contextvar", default=None)
)


def get_current_timeout() -> float | None:
    current_context_timeout = _timeout_contextvar.get()
    if not current_context_timeout:
        return None

    deadline = cast(float, current_context_timeout.when())

    return max(deadline - asyncio.get_running_loop().time(), 0)


@contextlib.asynccontextmanager
async def timeout(timeout: float | None = None) -> collections.abc.AsyncGenerator:
    if timeout is None:
        # timeout is None, no timeout needed,
        # so we do nothing and emulate nullcontext
        yield
        return

    timeout_obj = asyncio.timeout(timeout)
    current_timeout_obj = _timeout_contextvar.get()
    if current_timeout_obj and (
        cast(float, current_timeout_obj.when()) <= cast(float, timeout_obj.when())
    ):
        # timeout had been already set, so
        # we compare new incoming and existing timeout,
        # when new timeout is bigger we do noting and emulate nullcontext
        yield
        return

    async with timeout_obj:
        # we enforce and set timeout
        token = _timeout_contextvar.set(timeout_obj)

        try:
            yield
        finally:
            _timeout_contextvar.reset(token)


P = ParamSpec("P")
R = TypeVar("R")


def with_timeout(
    fn: collections.abc.Callable[P, collections.abc.Awaitable[R]],
    value: float | None = None,
) -> collections.abc.Callable[P, collections.abc.Awaitable[R]]:
    @functools.wraps(fn)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        async with timeout(value):
            return await fn(*args, **kwargs)

    return wrapped


async def wait_for(aw: collections.abc.Awaitable[R], timeout_: float) -> R:
    async with timeout(timeout_):
        return await aw


def max_timeout() -> asyncio.Timeout:
    ack_timeout = int(os.getenv("DELPHAI_RPC_RABBITMQ_ACK_TIMEOUT_SECONDS") or 30 * 60)

    # Should be at least 1 minute less than the RabbitMQ `consumer_timeout` value.
    # Reference: https://www.rabbitmq.com/docs/consumers#acknowledgement-timeout
    # Default is 29 minutes, while RabbitMQ `consumer_timeout` defaults to 30 minutes.
    max_timeout = max(ack_timeout - 60, 0)

    return asyncio.timeout(max_timeout)


@dataclasses.dataclass
class Codec:
    compress: Callable[[bytes], bytes]
    decompress: Callable[[bytes], bytes]
    detect: Callable[[bytes], bool]


CODECS: dict[str, Codec] = {
    "deflate": Codec(
        zlib.compress,
        zlib.decompress,
        lambda data: any(
            data.startswith(x)
            for x in (
                b"\x78\x01",
                b"\x78\x5e",
                b"\x78\x9c",
                b"\x78\xda",
            )
        ),
    ),
    "zstd": Codec(
        zstandard.compress,
        zstandard.decompress,
        lambda data: data.startswith(b"\x28\xb5\x2f\xfd"),
    ),
}


def get_encoding(data: bytes) -> str | None:
    for name, codec in CODECS.items():
        if codec.detect(data):
            return name

    return None


COMPRESS_MIN_SIZE = 1024 * 10
COMPRESS_MIN_RATE = 0.7


def compress(data: bytes, encoding: str) -> tuple[bytes, str | None]:
    codec = CODECS.get(encoding)
    if not codec:
        raise ValueError(f"Compression failed: unknown encoding `{encoding}`")

    compressed = codec.compress(data)
    if len(compressed) < len(data) * COMPRESS_MIN_RATE:
        return compressed, encoding

    return data, None


def decompress(data: bytes, encoding: str) -> bytes:
    codec = CODECS.get(encoding)
    if not codec:
        raise ValueError(f"Decompression failed: unknown encoding `{encoding}`")

    return codec.decompress(data)


ObjectId: Any = None
with contextlib.suppress(ImportError):
    from bson import ObjectId


MSGPACK_EXT_TYPE_OBJECT_ID = 1
MSGPACK_EXT_TYPE_UUID = 2


def _msgpack_default(obj: Any) -> msgpack.ExtType:
    if ObjectId and isinstance(obj, ObjectId):
        return msgpack.ExtType(MSGPACK_EXT_TYPE_OBJECT_ID, obj.binary)

    if isinstance(obj, uuid.UUID):
        return msgpack.ExtType(MSGPACK_EXT_TYPE_UUID, obj.bytes)

    raise TypeError(f"Cannot serialize {obj!r}")


def _msgpack_ext_hook(code: int, data: bytes) -> Any:
    if code == MSGPACK_EXT_TYPE_OBJECT_ID:
        if ObjectId is None:
            raise RuntimeError("Install `bson` package to support `ObjectId` type")

        return ObjectId(data)

    if code == MSGPACK_EXT_TYPE_UUID:
        return uuid.UUID(bytes=data)

    return msgpack.ExtType(code, data)


def msgpack_dumps(data: Any) -> bytes:
    return msgpack.dumps(
        data,
        datetime=True,
        default=_msgpack_default,
    )


def msgpack_loads(body: bytes) -> Any:
    return msgpack.loads(
        body,
        timestamp=3,
        ext_hook=_msgpack_ext_hook,
        strict_map_key=False,
    )
