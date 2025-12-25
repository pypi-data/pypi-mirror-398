class Exception(Exception):
    def __init__(self, message, device=None):
        if device is not None:
            device.stop_all()

        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
