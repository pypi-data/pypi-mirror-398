from abc import ABCMeta

from qtoggleserver.core import ports as core_ports

from . import constants
from .paradoxport import ParadoxPort
from .typing import Property


class AreaPort(ParadoxPort, metaclass=ABCMeta):
    def __init__(self, area: int, *args, **kwargs) -> None:
        self.area: int = area

        super().__init__(*args, **kwargs)

    def make_id(self) -> str:
        return f"area{self.area}.{self.ID}"

    def get_area_label(self) -> str:
        return self.get_property("label") or f"Area {self.area}"

    def get_property(self, name: str) -> Property | None:
        return self.get_peripheral().get_property("partition", self.area, name)

    def get_properties(self) -> dict[str, Property]:
        return self.get_peripheral().get_properties("partition", self.area)


class AreaArmedPort(AreaPort):
    TYPE = "number"
    WRITABLE = True
    CHOICES = [
        {"value": 1, "display_name": "Disarmed"},
        {"value": 2, "display_name": "Armed"},
        {"value": 3, "display_name": "Armed (Sleep)"},
        {"value": 4, "display_name": "Armed (Stay)"},
        {"value": -1, "display_name": "Disarming"},
        {"value": -2, "display_name": "Arming"},
        {"value": -3, "display_name": "Arming (Sleep)"},
        {"value": -4, "display_name": "Arming (Stay)"},
    ]

    ID = "armed"

    _DEFAULT_STATE = "disarmed"

    _ARMED_STATE_MAPPING = {
        "disarmed": 1,
        "armed_away": 2,
        "armed_night": 3,
        "armed_home": 4,
        "triggered": 5,
        1: "disarmed",
        2: "armed_away",
        3: "armed_night",
        4: "armed_home",
        5: "triggered",
    }

    _OPPOSITE_ARMED_STATE_MAPPING = {
        "disarmed": "armed_away",
        "armed_away": "disarmed",
        "armed_night": "disarmed",
        "armed_home": "disarmed",
    }

    _ARMED_MODE_MAPPING = {
        1: constants.ARMED_MODE_DISARMED,
        2: constants.ARMED_MODE_ARMED,
        3: constants.ARMED_MODE_ARMED_SLEEP,
        4: constants.ARMED_MODE_ARMED_STAY,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._requested_value: int | None = None  # used to cache written value while pending
        self._last_state: str = self.get_property("current_state") or self._DEFAULT_STATE
        self._last_non_pending_state: str = self._last_state

    async def attr_get_default_display_name(self) -> str:
        return f"{self.get_area_label()} Armed"

    async def read_value(self) -> int | None:
        current_state = self.get_property("current_state") or self._DEFAULT_STATE

        # Only act on transitions
        if current_state != self._last_state:
            self.debug("state transition: %s -> %s", self._last_state, current_state)
            self._last_state = current_state

            if current_state not in ("pending", "arming"):
                self._last_non_pending_state = current_state
                if self._requested_value is not None:  # pending value requested via qToggle
                    requested_state = self._ARMED_STATE_MAPPING[self._requested_value]
                    self._requested_value = None

                    if current_state == requested_state:
                        self.debug("requested state %s fulfilled", requested_state)
                    else:
                        self.debug("requested state %s not fulfilled", requested_state)

        # Decide upon returned value
        if self._requested_value is not None:
            return -self._requested_value
        else:
            if current_state in ("pending", "arming"):
                # If state is pending, but we don't have a requested value, it's probably arming/disarming via some
                # other external means. The best we can do is to indicate the opposite state as pending.
                opposite_state = self._OPPOSITE_ARMED_STATE_MAPPING.get(
                    self._last_non_pending_state, self._last_non_pending_state
                )
                return -self._ARMED_STATE_MAPPING[opposite_state]
            else:
                return self._ARMED_STATE_MAPPING[current_state]

    @core_ports.skip_write_unavailable
    async def write_value(self, value: int) -> None:
        self._requested_value = value
        await self.get_peripheral().set_area_armed_mode(self.area, self._ARMED_MODE_MAPPING[abs(value)])


class AreaAlarmPort(AreaPort):
    TYPE = "boolean"
    WRITABLE = False

    ID = "alarm"

    async def attr_get_default_display_name(self) -> str:
        return f"{self.get_area_label()} Alarm"

    async def read_value(self) -> bool | None:
        return self.get_property("alarm")
