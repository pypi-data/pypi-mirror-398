from rustpy.db_async import get_async_backend, is_async_configured
from .queryset_async import AsyncQuerySet

class AsyncManager:
    def __init__(self):
        self.model = None

    def contribute_to_class(self, model):
        self.model = model

    def __get__(self, instance, owner):
        if not is_async_configured():
            raise RuntimeError(
                "Async DB backend sozlanmagan. "
                "CLI yoki entry-point da setup_from_config() chaqiring."
            )

        backend = get_async_backend()
        return AsyncQuerySet(owner, backend)
