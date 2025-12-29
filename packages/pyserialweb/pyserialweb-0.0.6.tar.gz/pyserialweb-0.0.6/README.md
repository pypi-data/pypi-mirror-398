# PySerialWeb
A [Web Serial API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Serial_API) wrapper for [Pyodide](https://github.com/pyodide/pyodide) (wip)

Currently, this is a very limited implementation with just support for reading and writing. The control signals getters are set to just return `True`/the setters are a no-op. 

If you're using this in Chrome, you may need to enable <chrome://flags/#enable-experimental-web-platform-features> (Web Serial API) and <chrome://flags/#enable-experimental-webassembly-stack-switching> (JS promise integration)

Depending on the Python/Pyodide version you're using, you'll need to call this API/your entrypoint using `pyodide.runPythonSyncifying()`/`callSyncifying()` (Python 3.11, Pyodide 0.25.1) or `pyodide.runPythonAsync`/`callPromising()` (latest Pyodide version at the time of writing, untested and still marked as experimental)
