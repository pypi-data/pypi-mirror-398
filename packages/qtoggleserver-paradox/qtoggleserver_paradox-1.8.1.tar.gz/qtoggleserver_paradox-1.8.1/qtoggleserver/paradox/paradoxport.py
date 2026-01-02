import abc

from typing import cast

from qtoggleserver.peripherals import PeripheralPort

from .paradoxalarm import ParadoxAlarm
from .typing import Property


class ParadoxPort(PeripheralPort, metaclass=abc.ABCMeta):
    def on_property_change(
        self, type_: str, id_: str | None, property_: str, old_value: Property, new_value: Property
    ) -> None:
        pass

    def get_peripheral(self) -> ParadoxAlarm:
        return cast(ParadoxAlarm, super().get_peripheral())
