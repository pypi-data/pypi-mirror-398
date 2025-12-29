# rustpy/models/registry.py
class ModelRegistry:
    _apps = {}

    @classmethod
    def register(cls, model):
        module = model.__module__
        app = ".".join(module.split(".")[:2])

        cls._apps.setdefault(app, {})
        cls._apps[app][model.__name__] = model

    @classmethod
    def get_models(cls):
        all_models = [
            model
            for models in cls._apps.values()
            for model in models.values()
        ]
        return all_models
