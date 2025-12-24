class Message:
    def __init__(self, level: str, message: str, topic: str = "-"):
        self.level = level
        self.topic = topic
        self.message = message

    def __repr__(self) -> str:
        return f"{self.level.upper()}: {'[' +  self.topic + ']' if self.topic else ''} {self.message}"


class WarningMessage(Message):

    def __init__(self, message: str, topic: str = "-"):
        super().__init__("warning", message, topic)


class ErrorMessage(Message):

    def __init__(self, message: str, topic: str = "-"):
        super().__init__("error", message, topic)


class InfoMessage(Message):

    def __init__(self, message: str, topic: str = "-"):
        super().__init__("info", message, topic)
