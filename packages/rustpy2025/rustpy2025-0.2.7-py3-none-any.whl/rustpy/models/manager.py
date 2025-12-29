from rustpy.db import get_backend, is_configured
from .queryset import QuerySet

class Manager:
    def __init__(self):
        self.model = None

    def contribute_to_class(self, model):
        self.model = model

    def __get__(self, instance, owner):
        
        if not is_configured():
            raise RuntimeError(
                "DB backend sozlanmagan. "
                "CLI yoki entry-point da setup_from_config() yoki auto_setup() chaqiring."
            )

        backend = get_backend()
        return QuerySet(owner, backend)
