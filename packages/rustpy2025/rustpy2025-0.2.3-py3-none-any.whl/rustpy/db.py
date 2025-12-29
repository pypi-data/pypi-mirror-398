_backend = None

def set_backend(backend):
    global _backend
    _backend = backend

def get_backend():
    if _backend is None:
        raise RuntimeError("DB backend sozlanmagan")

    return _backend

def is_configured():
    return _backend is not None
