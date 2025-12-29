from .meta import ModelMeta
from .manager import Manager
from .manager_async import AsyncManager

class Model(metaclass=ModelMeta):
    _backend = None
    objects = Manager()
    aobjects = AsyncManager()

    @classmethod
    def bind_backend(cls, backend):
        cls._backend = backend

    def __init__(self, **kwargs):
        for fname, field in self._meta["fields"].items():
            value = kwargs.get(fname, field.default)
            setattr(self, fname, value)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"
