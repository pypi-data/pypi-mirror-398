from .fields import Field, ForeignKey
from .manager import Manager
from rustpy.models.registry import ModelRegistry


class ModelMeta(type):
    # print("ModelMeta metaclass initialized")
    def __new__(mcls, name, bases, attrs):

        if name == "Model":
            return super().__new__(mcls, name, bases, attrs)

        meta_fields = {}
        managers = {}

        for key, value in list(attrs.items()):
            if isinstance(value, Field) and not isinstance(value, ForeignKey):
                value.contribute_to_class(key)
                meta_fields[key] = value
                attrs.pop(key)

            elif isinstance(value, ForeignKey):
                value.contribute_to_class(key)
                meta_fields[value.column_name] = value
                attrs.pop(key)

            elif isinstance(value, Manager):
                managers[key] = value

        meta = attrs.pop("Meta", None)
        table_name = getattr(meta, "db_table", name.lower())

        cls = super().__new__(mcls, name, bases, attrs)

        cls._meta = {
            "table": table_name,
            "fields": meta_fields,
        }

        # 🔥 ENG MUHIM QATOR
        ModelRegistry.register(cls)

        for manager in managers.values():
            manager.contribute_to_class(cls)

        return cls
