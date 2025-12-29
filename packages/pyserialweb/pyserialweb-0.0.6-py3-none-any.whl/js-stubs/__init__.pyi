from collections.abc import Callable, Iterable
from typing import Any, Awaitable, Literal, Optional, TypedDict, overload

from _pyodide._core_docs import _JsProxyMetaClass
from pyodide.ffi import (
    JsArray,
    JsDomElement,
    JsException,
    JsFetchResponse,
    JsProxy,
    JsTypedArray,
)
from pyodide.webloop import PyodideFuture

_portHandle = SerialPort

# in browser the cancellation token is an int, in node it's a special opaque
# object.
_CancellationToken = int | JsProxy

def setTimeout(
    cb: Callable[[], Any], timeout: int | float
) -> _CancellationToken: ...
def clearTimeout(id: _CancellationToken) -> None: ...
def setInterval(
    cb: Callable[[], Any], interval: int | float
) -> _CancellationToken: ...
def clearInterval(id: _CancellationToken) -> None: ...
def fetch(
    url: str, options: JsProxy | None = None
) -> PyodideFuture[JsFetchResponse]: ...

self: Any = ...
window: Any = ...

# Shenanigans to convince skeptical type system to behave correctly:
#
# These classes we are declaring are actually JavaScript objects, so the class
# objects themselves need to be instances of JsProxy. So their type needs to
# subclass JsProxy. We do this with a custom metaclass.

class _JsMeta(_JsProxyMetaClass, JsProxy):
    pass

class _JsObject(metaclass=_JsMeta):
    pass

class XMLHttpRequest(_JsObject):
    response: str

    @staticmethod
    def new() -> XMLHttpRequest: ...
    def open(self, method: str, url: str, sync: bool) -> None: ...
    def send(self, body: JsProxy | None = None) -> None: ...

class Object(_JsObject):
    @staticmethod
    def fromEntries(it: Iterable[JsArray[Any]]) -> JsProxy: ...

class Array(_JsObject):
    @staticmethod
    def new() -> JsArray[Any]: ...

class ImageData(_JsObject):
    @staticmethod
    def new(
        width: int, height: int, settings: JsProxy | None = None
    ) -> ImageData: ...

    width: int
    height: int

class JSON(_JsObject):
    @staticmethod
    def stringify(a: JsProxy) -> str: ...
    @staticmethod
    def parse(a: str) -> JsProxy: ...

class console(_JsObject):
    @staticmethod
    def debug(*args: Any): ...
    @staticmethod
    def info(*args: Any): ...
    @staticmethod
    def log(*args: Any): ...
    @staticmethod
    def warn(*args: Any): ...
    @staticmethod
    def error(*args: Any): ...

class document(_JsObject):
    body: JsDomElement
    children: list[JsDomElement]
    @overload
    @staticmethod
    def createElement(tagName: Literal["canvas"]) -> JsCanvasElement: ...
    @overload
    @staticmethod
    def createElement(tagName: str) -> JsDomElement: ...
    @staticmethod
    def appendChild(child: JsDomElement) -> None: ...

class JsCanvasElement(JsDomElement):
    width: int | float
    height: int | float
    def getContext(
        self,
        ctxType: str,
        *,
        powerPreference: str = "",
        premultipliedAlpha: bool = False,
        antialias: bool = False,
        alpha: bool = False,
        depth: bool = False,
        stencil: bool = False,
    ) -> Any: ...

class ArrayBuffer(_JsObject):
    @staticmethod
    def isView(x: Any) -> bool: ...

class DOMException(JsException):
    pass

class Map:
    @staticmethod
    def new(a: Iterable[Any]) -> Map: ...

async def sleep(ms: int | float) -> None: ...

class AbortSignal(_JsObject):
    @staticmethod
    def any(iterable: Iterable[AbortSignal]) -> AbortSignal: ...
    @staticmethod
    def timeout(ms: int) -> AbortSignal: ...
    aborted: bool
    reason: JsException
    def throwIfAborted(self): ...
    def onabort(self): ...

class AbortController(_JsObject):
    @staticmethod
    def new() -> AbortController: ...
    signal: AbortSignal
    def abort(self, reason: JsException | None = None) -> None: ...

class Response(_JsObject):
    @staticmethod
    def new(body: Any) -> Response: ...

class Promise(_JsObject):
    @staticmethod
    def resolve(value: Any) -> Promise: ...

class ReadResult(TypedDict):
    value: JsTypedArray
    done: bool

class Uint8Array(JsTypedArray):
    pass

class ReadableStreamDefaultReader(ReadableStream):
    def read(self) -> Awaitable[ReadResult]: ...
    def releaseLock(self) -> None: ...

class ReadableStream(_JsObject):
    def getReader(self) -> ReadableStreamDefaultReader: ...

class WritableStreamDefaultWriter(_JsObject):
    def write(self, chunk: JsTypedArray) -> Awaitable[None]: ...
    def releaseLock(self) -> None: ...

class WritableStream(_JsObject):
    def getWriter(self) -> WritableStreamDefaultWriter: ...

class SerialOptions(TypedDict):
    baudRate: int
    dataBits: Optional[Literal[7] | Literal[8]]
    stopBits: Optional[Literal[1] | Literal[2]]
    parity: Optional[Literal["none"] | Literal["even"] | Literal["odd"]]
    bufferSize: Optional[int]
    flowControl: Optional[Literal["none"] | Literal["hardware"]]

class SerialPortInfo(TypedDict):
    usbVendorId: Optional[int]
    usbProductId: Optional[int]

class SerialInputSignals(TypedDict):
    dataCarrierDetect: bool
    clearToSend: bool
    ringIndicator: bool
    dataSetReady: bool

class SerialOutputSignals(TypedDict, total=False):
    dataTerminalReady: bool
    requestToSend: bool
    break_: bool

class SerialPort(_JsObject):
    readable: ReadableStream
    writable: WritableStream
    def open(self, options: _JsObject) -> Awaitable[None]: ...
    def close(self) -> Awaitable[None]: ...
    def getInfo(self) -> SerialPortInfo: ...
    def forget(self) -> Awaitable[None]: ...
    def getSignals(self) -> Awaitable[SerialInputSignals]: ...
    def setSignals(self, signals: SerialOutputSignals) -> Awaitable[None]: ...

class navigator(_JsObject):
    class serial(_JsObject):
        @staticmethod
        def getPorts() -> Awaitable[list[SerialPort]]: ...
        @staticmethod
        def requestPort(
            options: Optional[Any] = None,
        ) -> Awaitable[SerialPort]: ...
