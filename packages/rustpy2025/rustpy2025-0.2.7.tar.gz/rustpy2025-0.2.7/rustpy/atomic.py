from contextlib import contextmanager
from rustpy.db import get_backend
from rustpy.tx_state import in_transaction, set_transaction

@contextmanager
def atomic():
    backend = get_backend()

    if in_transaction():
        yield
        return

    try:
        set_transaction(True)
        backend.begin()
        yield
        backend.commit()
    except Exception:
        backend.rollback()
        raise
    finally:
        set_transaction(False)
