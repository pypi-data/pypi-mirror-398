class MediaMuncherError(Exception):
    def __init__(self, message, original_message=None):
        self.message = message
        self.original_message = original_message
        super().__init__(message)

class MediaHandlerError(MediaMuncherError):
    def __init__(self, message, original_message=None):
        super().__init__(message, original_message)
