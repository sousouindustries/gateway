

class GatewayException(Exception):
    DEFAULT_REASON = "Please contact the system administrator for further information."

    def __init__(self, reason=None):
        self.reason = reason or self.DEFAULT_REASON
