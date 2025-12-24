import importlib
import pkgutil

from media_muncher.profile.schemas.base import BaseSchemaGenerator


class SchemaGeneratorFactory:
    _generators = {}

    @classmethod
    def _discover_generators(cls):
        if cls._generators:
            return  # Already discovered

        package = importlib.import_module("media_muncher.profile.schemas")
        prefix = package.__name__ + "."

        for _, module_name, _ in pkgutil.iter_modules(package.__path__, prefix):
            module = importlib.import_module(module_name)
            for attr in dir(module):
                obj = getattr(module, attr)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseSchemaGenerator)
                    and obj is not BaseSchemaGenerator
                ):
                    schema_name = getattr(obj, "schema_name", None)
                    if schema_name:
                        cls._generators[schema_name] = obj

    @classmethod
    def create_generator(
        cls, schema_name: str, config: dict, messages: list
    ) -> BaseSchemaGenerator:
        cls._discover_generators()
        generator_class = cls._generators.get(schema_name)
        if not generator_class:
            raise ValueError(f"Unknown profile schema: {schema_name}")
        return generator_class(config, messages)
