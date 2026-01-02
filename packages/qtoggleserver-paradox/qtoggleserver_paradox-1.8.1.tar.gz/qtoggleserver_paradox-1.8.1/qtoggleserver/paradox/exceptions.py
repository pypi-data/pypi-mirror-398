class ParadoxException(Exception):
    pass


class ParadoxConnectError(ParadoxException):
    def __init__(self) -> None:
        super().__init__("Unable to connect to panel")


class ParadoxCommandError(ParadoxException):
    pass


class ParadoxTimeout(ParadoxException):
    pass
