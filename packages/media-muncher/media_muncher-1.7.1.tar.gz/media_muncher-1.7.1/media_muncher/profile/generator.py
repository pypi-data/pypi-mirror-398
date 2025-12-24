from media_muncher.profile.factory import SchemaGeneratorFactory


class ABRProfileGenerator:
    def __init__(self, schema: str, **kwargs) -> None:
        self.config = {
            "preset": "veryfast",
            "schema": schema,
            # "framerate": 25,
        }
        self.config.update(kwargs)
        self.messages = []

        # Initialize the appropriate schema generator using the factory
        self.schema_generator = SchemaGeneratorFactory.create_generator(
            self.config["schema"], self.config, self.messages
        )

    def generate(self, renditions, packaging, name: str = ""):
        return self.schema_generator.generate(renditions, packaging, name)
