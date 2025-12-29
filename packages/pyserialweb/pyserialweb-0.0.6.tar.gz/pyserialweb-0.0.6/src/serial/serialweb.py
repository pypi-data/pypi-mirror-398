import asyncio
import js

import pyodide.ffi
import typing

from .serialutil import (
    SerialBase,
    to_bytes,
    PortNotOpenError,
)


def run_sync(js_coro):
    if hasattr(pyodide.ffi, "to_sync"):
        return pyodide.ffi.to_sync(js_coro)  # type: ignore
    else:
        js.console.log(f"Running {js_coro}")
        return js_coro.syncify()  # type: ignore


def convert_dict_to_js(inp: dict) -> js.Object:
    return typing.cast(
        js.Object, js.Object.fromEntries(pyodide.ffi.to_js(inp))
    )


class Serial(SerialBase):
    """Serial port implementation for Emscripten based on the Web Serial API."""

    def __init__(self, *args, **kwargs):
        super(Serial, self).__init__(*args, **kwargs)

    def open(self):
        js.console.debug("start open")
        if not hasattr(js, "_portHandle"):
            js.console.log("reconfigure port")
            js._portHandle = typing.cast(
                js.SerialPort, run_sync(js.navigator.serial.requestPort())
            )
            js.console.log(js._portHandle)
        elif self.is_open:
            js.console.debug("already open internally, skipping")
            return
        js.console.debug("finished open checks")
        if not hasattr(js, "_portHandle"):
            raise RuntimeError("No port selected!")
        if not self.baudrate:
            js.console.debug("setting baudrate to 9600")
            self.baudrate = 9600
        try:
            js.console.debug("trying to open port")
            run_sync(
                js._portHandle.open(
                    convert_dict_to_js(
                        {
                            "baudRate": self.baudrate,
                            "dataBits": None,
                            "parity": None,
                            "bufferSize": None,
                            "flowControl": None,
                            "stopBits": None,
                        }
                    )
                )
            )
        except Exception as e:
            js.console.debug("caught exception in open")
            if "already open" in str(e):
                js.console.log("Port was already open, skipping")
            else:
                e.add_note("Error while trying open port")
                js.console.error(e)
                raise e
        self.is_open = True
        js.console.debug("finish open")

    def __del__(self):
        self.close()

    def close(self):
        js.console.debug("close stub")
        pass
        # if not self.is_open:
        #     return
        # run_sync(js._portHandle.close())

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    @property
    def in_waiting(self):
        # info not provided by WritableStream since the queue implementation can be browser-specific
        return 0

    def read(self, size=1) -> bytes:
        """\
        Read size bytes from the serial port. If a timeout is set it may
        return less characters as requested. With no timeout it will block
        until the requested number of bytes is read.
        """
        js.console.debug(f"start read, size={size}")
        if not self.is_open:
            raise PortNotOpenError()
        if size <= 0:
            return bytes()
        reader = js._portHandle.readable.getReader()
        buffer = bytearray()
        while len(buffer) < size:
            result = run_sync(reader.read())
            js.console.debug("Got data", result)
            value = result.value
            if not value:
                break
            buffer.extend(value)
            if result.done:
                break
        reader.releaseLock()
        js.console.debug("finish read")
        return buffer

    def write(self, data) -> int:
        """Output the given byte string over the serial port."""
        js.console.debug("start write")
        if not self.is_open:
            raise PortNotOpenError()
        bytes = to_bytes(data)
        if not bytes:
            return 0
        writer = js._portHandle.writable.getWriter()
        run_sync(
            writer.write(
                typing.cast(
                    pyodide.ffi.JsTypedArray,
                    js.Uint8Array.new(pyodide.ffi.to_js(bytes)),
                )
            )
        )
        writer.releaseLock()
        js.console.debug("finish write")
        return len(bytes)

    def flush(self):
        """\
        Flush of file like objects. In this case, wait until all data
        is written.
        """
        js.console.debug("flush")
        pass

    def reset_input_buffer(self):
        """Clear input buffer, discarding all that is in the buffer."""
        pass

    def reset_output_buffer(self):
        """\
        Clear output buffer, aborting the current output and discarding all
        that is in the buffer.
        """
        pass

    @property
    def cts(self):
        """Read terminal status line: Clear To Send"""
        return True

    @property
    def dsr(self):
        """Read terminal status line: Data Set Ready"""
        return True

    @property
    def ri(self):
        """Read terminal status line: Ring Indicator"""
        return True

    @property
    def cd(self):
        """Read terminal status line: Carrier Detect"""
        return True

    # - - platform specific - - - -

    def set_buffer_size(self, rx_size=4096, tx_size=None):
        """\
        Recommend a buffer size to the driver (device driver can ignore this
        value). Must be called after the port is opened.
        """
        pass

    def set_output_flow_control(self, enable=True):
        """\
        Manually control flow - when software flow control is enabled.
        This will do the same as if XON (true) or XOFF (false) are received
        from the other device and control the transmission accordingly.
        WARNING: this function is not portable to different platforms!
        """
        pass

    @property
    def out_waiting(self):
        """Return how many bytes the in the outgoing buffer"""
        return 0

    def cancel_read(self):
        """Cancel a blocking read operation, may be called from other thread"""
        pass

    def cancel_write(self):
        """Cancel a blocking write operation, may be called from other thread"""
        pass
