import time

from abc import ABCMeta

from .paradoxport import ParadoxPort
from .typing import Property


class RemotePort(ParadoxPort, metaclass=ABCMeta):
    def __init__(self, remote: int, *args, **kwargs) -> None:
        self.remote: int = remote

        super().__init__(*args, **kwargs)

    def make_id(self) -> str:
        return f"remote{self.remote}.{self.ID}"

    def get_remote_label(self) -> str:
        return self.get_property("label") or f"Remote {self.remote}"

    def get_property(self, name: str) -> Property:
        return self.get_peripheral().get_property("user", self.remote, name)

    def get_properties(self) -> dict[str, Property]:
        return self.get_peripheral().get_properties("user", self.remote)


class RemoteButtonPort(RemotePort):
    TYPE = "boolean"
    WRITABLE = False

    ID = "button"

    def __init__(self, button: str, timeout: int, *args, **kwargs) -> None:
        self.button: str = button
        self.timeout: int = timeout
        self.last_button_value: int = 0
        self.change_timestamp: int = 0

        super().__init__(*args, **kwargs)

    def make_id(self) -> str:
        return f"{super().make_id()}_{self.button}"

    async def attr_get_default_display_name(self) -> str:
        return f"{super().get_remote_label()} Button {self.button.upper()}"

    async def read_value(self) -> bool:
        now = int(time.time() * 1000)
        value = self.get_button_value()
        if value and value != self.last_button_value:
            self.debug("button value changed from %s to %s", self.last_button_value, value)
            self.last_button_value = value
            self.change_timestamp = now

        return now - self.change_timestamp <= self.timeout

    def get_button_value(self) -> int:
        return self.get_property(f"button_{self.button}") or 0


class AnyRemoteButtonPort(RemotePort):
    TYPE = "boolean"
    WRITABLE = False

    ID = "button"

    def __init__(self, remotes: list[int], button: str, timeout: int, *args, **kwargs) -> None:
        self.remotes: list[int] = remotes
        self.button: str = button
        self.timeout: int = timeout
        self.last_button_values: dict[int, int] = {}
        self.change_timestamps: dict[int, int] = {}

        super().__init__(remote=0, *args, **kwargs)

    def make_id(self) -> str:
        return f"remote.{self.ID}_{self.button}"

    async def attr_get_default_display_name(self) -> str:
        return f"Remote Button {self.button.upper()}"

    async def read_value(self) -> bool:
        now = int(time.time() * 1000)
        for remote in self.remotes:
            value = self.get_button_value(remote)
            last_value = self.last_button_values.get(remote, 0)
            if value and value != last_value:
                self.debug("button value changed from %s to %s on remote %s", last_value, value, remote)
                self.last_button_values[remote] = value
                self.change_timestamps[remote] = now

        for remote in self.remotes:
            if now - self.change_timestamps.get(remote, 0) <= self.timeout:
                return True

        return False

    def get_button_value(self, remote: int) -> int:
        return self.get_peripheral().get_property("user", remote, f"button_{self.button}")
