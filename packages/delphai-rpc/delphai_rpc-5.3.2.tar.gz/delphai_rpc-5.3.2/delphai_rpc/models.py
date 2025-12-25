import asyncio
import collections
import enum
import logging
from typing import Any, ClassVar, Generic, Literal, Self, TypeVar

import pydantic

from . import errors, utils

logger = logging.getLogger(__name__)


class BaseModel(pydantic.BaseModel):
    type: ClassVar[str]

    def model_dump_msgpack(self, **kwargs: Any) -> bytes:
        kwargs.setdefault("exclude_defaults", True)
        data = self.model_dump(**kwargs)
        return utils.msgpack_dumps(data)

    def model_dump_message(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "body": self.model_dump_msgpack(**kwargs),
            "content_type": "application/msgpack",
            "type": self.type,
        }

    @classmethod
    def model_validate_msgpack(cls, body: bytes) -> Self:
        try:
            return cls.model_validate(utils.msgpack_loads(body))
        except ValueError as error:
            raise errors.BadMessageError(f"Message deserialization failed: `{error!r}`")

    @classmethod
    def model_validate_message(
        cls,
        body: bytes,
        message_type: str,
        content_type: str | None = None,
        **kwargs: Any,
    ) -> Self:
        if message_type != cls.type:
            raise errors.BadMessageError(f"Wrong message type `{message_type}`")

        if content_type != "application/msgpack":
            raise errors.BadMessageError(
                f"Got a message with unknown content type: {content_type}"
            )

        return cls.model_validate_msgpack(body=body)


class Request(BaseModel):
    type = "rpc.request"
    method_name: str
    arguments: dict[str, Any] = {}
    context: bytes | None = None
    timings: list[tuple[str, float]] = []


class ResponseError(pydantic.BaseModel):
    type: str
    message: str | None = None

    @classmethod
    def build_from_error(cls, error: Exception) -> Self:
        if isinstance(error, errors.RpcError):
            return cls(type=type(error).__name__, message=error.args[0])

        return cls(type="UnknownError", message=repr(error))

    def as_exception(self) -> errors.RpcError:
        error_class = getattr(errors, self.type, errors.UnknownError)
        return error_class(self.message)


ResultType = TypeVar("ResultType")


class Result(BaseModel, Generic[ResultType]):
    result: ResultType | None = None
    error: ResponseError | None = None

    @classmethod
    def build_from_error(cls, error: Exception) -> Self:
        return cls(error=ResponseError.build_from_error(error))

    def as_future(self) -> asyncio.Future[ResultType]:
        if self.result is None and self.error is None:
            raise RuntimeError("Cannot build Future due no result or error")

        future: asyncio.Future[ResultType] = asyncio.Future()

        if self.error:
            future.set_exception(self.error.as_exception())
            return future

        assert self.result
        future.set_result(self.result)

        return future


class Response(Result):
    type = "rpc.response"
    context: bytes | None = None
    timings: list[tuple[str, float]] = []


TAbstractOptions = TypeVar("TAbstractOptions", bound="AbstractOptions")


class AbstractOptions(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

    def __init__(self, *args: "AbstractOptions", **kwargs: dict[str, Any]) -> None:
        if args:
            merged = {}
            self_class = type(self)
            for options in args:
                if not isinstance(options, self_class):
                    raise TypeError(
                        f"Positional arguments must be {self_class} instances"
                    )

                merged.update(options.model_dump(exclude_unset=True))
            merged.update(**kwargs)

            kwargs = merged

        super().__init__(**kwargs)

    def update(self, *args: "TAbstractOptions", **kwargs: Any) -> Self:
        if not args and not kwargs:
            return self

        return self.__class__(self, *args, **kwargs)


class Priority(enum.IntEnum):
    LOW = 0
    NORMAL = 1
    DEFAULT = 1
    HIGH = 2
    INTERACTIVE = 3
    SYSTEM = 4


class Options(AbstractOptions):
    timeout: float | None = 60
    priority: Priority | None = None
    no_wait: bool = False
    retry: bool | dict = False


class RpcCall(pydantic.BaseModel, Generic[ResultType]):
    # Label to distinguish an RpcCall-serializable dict from a regular one
    type: Literal["RpcCall_6f3a73776c"]

    service_name: str
    method_name: str
    arguments: dict[str, Any] = {}
    options: Options = Options()
    result: Result[ResultType] | None = None

    coroutine_function: collections.abc.Callable | None = pydantic.Field(
        default=None,
        exclude=True,
    )

    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        return cls(**kwargs, type="RpcCall_6f3a73776c")

    @property
    def is_done(self) -> bool:
        return self.result is not None

    def __await__(self) -> collections.abc.Generator[Any, None, Any]:
        if self.result is None and self.coroutine_function is None:
            raise RuntimeError(
                "Cannot await an `RpcCall` with no result or coroutine function"
            )

        if self.coroutine_function:
            coroutine = self.coroutine_function(
                service_name=self.service_name,
                method_name=self.method_name,
                arguments=self.arguments,
                options=self.options,
            )

            return coroutine.__await__()

        assert self.result
        future = self.result.as_future()
        self.result = None

        return future.__await__()

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"service={self.service_name}, "
            f"method={self.method_name}, "
            f"done={self.is_done})"
        )

    __hash__ = object.__hash__
