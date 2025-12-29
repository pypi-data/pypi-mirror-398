import contextvars

_in_tx = contextvars.ContextVar("in_tx", default=False)

def in_transaction():
    return _in_tx.get()

def set_transaction(val: bool):
    _in_tx.set(val)
