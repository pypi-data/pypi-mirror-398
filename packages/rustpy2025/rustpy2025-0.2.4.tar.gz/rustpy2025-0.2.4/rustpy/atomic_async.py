from contextlib import asynccontextmanager
from rustpy.db_async import get_async_backend
from rustpy.tx_state import set_transaction

@asynccontextmanager
async def atomic():
    backend = get_async_backend()

    try:
        set_transaction(True)
        await backend.abegin()

        yield

        await backend.acommit()

    except Exception as e:
        await backend.arollback()
        raise

    finally:
        set_transaction(False)
