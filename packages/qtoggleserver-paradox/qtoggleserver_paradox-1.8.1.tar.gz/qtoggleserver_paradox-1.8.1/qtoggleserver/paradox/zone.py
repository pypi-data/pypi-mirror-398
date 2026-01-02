from abc import ABCMeta

from .paradoxport import ParadoxPort
from .typing import Property


class ZonePort(ParadoxPort, metaclass=ABCMeta):
    def __init__(self, zone: int, *args, **kwargs) -> None:
        self.zone: int = zone

        super().__init__(*args, **kwargs)

    def make_id(self) -> str:
        return f"zone{self.zone}.{self.ID}"

    def get_zone_label(self) -> str:
        return self.get_property("label") or f"Zone {self.zone}"

    def get_property(self, name: str) -> Property:
        return self.get_peripheral().get_property("zone", self.zone, name)

    def get_properties(self) -> dict[str, Property]:
        return self.get_peripheral().get_properties("zone", self.zone)


class ZoneOpenPort(ZonePort):
    TYPE = "boolean"
    WRITABLE = False

    ID = "open"

    async def attr_get_default_display_name(self) -> str:
        return f"{self.get_zone_label()} Open"

    async def read_value(self) -> bool | None:
        return self.get_property("open")


class ZoneAlarmPort(ZonePort):
    TYPE = "boolean"
    WRITABLE = False

    ID = "alarm"

    async def attr_get_default_display_name(self) -> str:
        return f"{self.get_zone_label()} Alarm"

    async def read_value(self) -> bool | None:
        return self.get_property("alarm")


class ZoneTroublePort(ZonePort):
    TYPE = "boolean"
    WRITABLE = False

    ID = "trouble"

    async def attr_get_default_display_name(self) -> str:
        return f"{self.get_zone_label()} Trouble"

    async def read_value(self) -> bool:
        for name, value in self.get_properties().items():
            if name.endswith("_trouble") and value:
                return True

        return False


class ZoneTamperPort(ZonePort):
    TYPE = "boolean"
    WRITABLE = False

    ID = "tamper"

    async def attr_get_default_display_name(self) -> str:
        return f"{self.get_zone_label()} Tamper"

    async def read_value(self) -> bool | None:
        return self.get_property("tamper")
