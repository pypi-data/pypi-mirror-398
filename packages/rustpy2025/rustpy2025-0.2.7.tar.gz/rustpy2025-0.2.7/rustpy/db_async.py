_async_backend = None

def set_async_backend(backend):
    global _async_backend
    _async_backend = backend

def get_async_backend():
    if _async_backend is None:
        raise RuntimeError("Async DB backend sozlanmagan")
    return _async_backend

def is_async_configured():
    return _async_backend is not None
