class Handshake_exception(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class Initial_workflow_exception(Handshake_exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class KMS_exception(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class Config_exception(Exception):
    def __init__(self, message: str):
        super().__init__(f"Invalid configuration: {message}")


class Communicator_exception(Exception):
    def __init__(self, message: str):
        super().__init__(f"{message}")


class Connection_timeout(Communicator_exception):
    def __init__(self, timeout_seconds: int):
        super().__init__(f"Connection has timed out after {timeout_seconds}s")


class Rotation_exception(Exception):
    def __init__(self, message: str):
        super().__init__(f"{message}")


class KEM_not_supported_exception(Exception):
    def __init__(self, kem: str):
        super().__init__(f"{kem}")

class No_cookie_set_for_peer_exception(Exception):
    def __init__(self, message: str):
        super().__init__(f"{message}")