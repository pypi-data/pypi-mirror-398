import asyncio
import logging

from types import SimpleNamespace
from typing import Any, cast

from qtoggleserver.peripherals import Peripheral
from qtoggleserver.utils import json as json_utils

from paradox.config import config
from paradox.lib import encodings, ps
from paradox.paradox import Paradox

from . import constants, exceptions
from .typing import Property


class ParadoxAlarm(Peripheral):
    SUPERVISOR_LOOP_INTERVAL = 5

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        *,
        areas: list[int] = None,
        zones: list[int] = None,
        outputs: list[int] = None,
        remotes: list[int] = None,
        remote_buttons: dict[str, str] = None,
        remote_buttons_timeout: int = constants.DEFAULT_REMOTE_BUTTONS_TIMEOUT,
        serial_port: str | None = None,
        serial_baud: int = constants.DEFAULT_SERIAL_BAUD,
        ip_host: str | None = None,
        ip_port: int = constants.DEFAULT_IP_PORT,
        ip_password: str = constants.DEFAULT_IP_PASSWORD,
        panel_password: str = constants.DEFAULT_PANEL_PASSWORD,
        **kwargs,
    ) -> None:
        self.setup_config()
        self.setup_logging()

        self._areas: list[int] = areas or []
        self._zones: list[int] = zones or []
        self._outputs: list[int] = outputs or []
        self._remotes: list[int] = remotes or []
        self._remote_buttons: dict[int, str] = {int(k): v for k, v in (remote_buttons or {}).items()}
        self._remote_buttons_timeout: int = remote_buttons_timeout

        self._serial_port: str | None = serial_port
        self._serial_baud: int = serial_baud
        self._ip_host: str | None = ip_host
        self._ip_port: int = ip_port
        self._ip_password: str = ip_password
        self._panel_password: str = panel_password

        self._paradox = None
        self._panel_task = None
        self._supervisor_task = asyncio.create_task(self._supervisor_loop())

        ps.subscribe(self.handle_paradox_property_change, "changes")

        self._properties = {}

        super().__init__(**kwargs)

    @staticmethod
    def setup_config() -> None:
        config.CONFIG_LOADED = True
        for k, v in config.DEFAULTS.items():
            if isinstance(v, tuple):
                v = v[0]

            setattr(config, k, v)

        config.SYNC_TIME = True
        encodings.register_encodings()

    @staticmethod
    def setup_logging() -> None:
        logging.getLogger("PAI").setLevel(logging.ERROR)
        logging.getLogger("PAI.paradox.lib.async_message_manager").setLevel(logging.CRITICAL)
        logging.getLogger("PAI.paradox.lib.handlers").setLevel(logging.CRITICAL)

    def make_paradox(self) -> Paradox:
        if self._serial_port:
            config.CONNECTION_TYPE = "Serial"
            config.SERIAL_PORT = self._serial_port
            config.SERIAL_BAUD = self._serial_baud
            config.IO_TIMEOUT = 10
            config.LOGGING_DUMP_PACKETS = True
            config.LOGGING_DUMP_MESSAGES = True

            self.debug("using serial connection on %s:%s", config.SERIAL_PORT, config.SERIAL_BAUD)
        else:  # IP connection, e.g. 192.168.1.2:10000:paradox
            config.CONNECTION_TYPE = "IP"
            config.IP_CONNECTION_HOST = self._ip_host
            config.IP_CONNECTION_PORT = self._ip_port
            config.IP_CONNECTION_PASSWORD = self._ip_password.encode()
            config.IP_INTERFACE_PASSWORD = self._ip_password.encode()

            self.debug("using IP connection on %s:%s", config.IP_CONNECTION_HOST, config.IP_CONNECTION_PORT)

        config.PASSWORD = self._panel_password.encode()

        return Paradox()

    def parse_labels(self) -> None:
        for area in self._paradox.storage.data["partition"].values():
            self.debug("detected area id=%s, label=%s", area["id"], json_utils.dumps(area["label"]))

        for zone in self._paradox.storage.data["zone"].values():
            self.debug("detected zone id=%s, label=%s", zone["id"], json_utils.dumps(zone["label"]))

        for output in self._paradox.storage.data["pgm"].values():
            self.debug("detected output id=%s, label=%s", output["id"], json_utils.dumps(output["label"]))

        for type_, entries in self._paradox.storage.data.items():
            for entry in entries.values():
                if "label" in entry:
                    self._properties.setdefault(type_, {}).setdefault(entry["id"], {})["label"] = entry["label"]

    async def connect(self) -> None:
        self.debug("connecting to panel")

        if not self._paradox:
            self._paradox = self.make_paradox()

        if not await self._paradox.full_connect():
            raise exceptions.ParadoxConnectError()

        self.debug("connected to panel")
        await self.handle_connected()

    async def make_port_args(self) -> list[dict[str, Any]]:
        from .area import AreaAlarmPort, AreaArmedPort
        from .output import OutputTamperPort, OutputTroublePort
        from .remote import AnyRemoteButtonPort, RemoteButtonPort
        from .system import SystemTroublePort
        from .zone import ZoneAlarmPort, ZoneOpenPort, ZoneTamperPort, ZoneTroublePort

        port_args = []
        port_args += [{"driver": AreaAlarmPort, "area": area} for area in self._areas]
        port_args += [{"driver": AreaArmedPort, "area": area} for area in self._areas]
        port_args += [{"driver": OutputTamperPort, "output": output} for output in self._outputs]
        port_args += [{"driver": OutputTroublePort, "output": output} for output in self._outputs]
        port_args += [{"driver": ZoneAlarmPort, "zone": zone} for zone in self._zones]
        port_args += [{"driver": ZoneOpenPort, "zone": zone} for zone in self._zones]
        port_args += [{"driver": ZoneTamperPort, "zone": zone} for zone in self._zones]
        port_args += [{"driver": ZoneTroublePort, "zone": zone} for zone in self._zones]
        port_args += [{"driver": SystemTroublePort}]

        for remote in self._remotes:
            for button in self._remote_buttons.get(remote, []):
                port_args.append(
                    {
                        "driver": RemoteButtonPort,
                        "remote": remote,
                        "button": button,
                        "timeout": self._remote_buttons_timeout,
                    }
                )

        any_remote_buttons = self._remote_buttons.get(0, [])
        for button in any_remote_buttons:
            port_args.append(
                {
                    "driver": AnyRemoteButtonPort,
                    "remotes": self._remotes,
                    "button": button,
                    "timeout": self._remote_buttons_timeout,
                }
            )

        return port_args

    async def handle_connected(self) -> None:
        self._panel_task = asyncio.create_task(self._paradox.loop())

        self.parse_labels()
        await self.trigger_port_update()

    async def disconnect(self) -> None:
        if self._panel_task is None:
            return

        self.debug("disconnecting")
        try:
            await self._paradox.disconnect()
        except ConnectionError as e:
            # PAI may raise ConnectionError when disconnecting, so we catch it here and ignore it
            self.error("failed to disconnect from panel: %s", e, exc_info=True)

        self._paradox = None

        await self.trigger_port_update()

        try:
            await asyncio.wait_for(self._panel_task, timeout=10)
        except TimeoutError:
            self.error("timeout waiting for panel task end")
            self._panel_task.cancel()
        else:
            self.debug("disconnected")

        self._panel_task = None

    async def _supervisor_loop(self) -> None:
        connect_succeeded = False

        while True:
            try:
                connected = (
                    self._paradox
                    and self._paradox.connection
                    and self._paradox.connection.connected
                    and connect_succeeded
                )

                self.set_online(connected)

                if self.is_enabled() and not connected:
                    try:
                        await self.connect()
                        connect_succeeded = True
                    except Exception as e:
                        self.error("failed to connect: %s", e, exc_info=True)
                elif not self.is_enabled() and connected:
                    connect_succeeded = False

                    try:
                        await self.disconnect()
                    except Exception as e:
                        self.error("failed to disconnect: %s", e, exc_info=True)

                if self._paradox:
                    self._update_properties()

                await asyncio.sleep(self.SUPERVISOR_LOOP_INTERVAL)
            except Exception as e:
                self.error("supervisor loop error: %s", e, exc_info=True)
                await asyncio.sleep(self.SUPERVISOR_LOOP_INTERVAL)
            except asyncio.CancelledError:
                self.debug("supervisor task cancelled")
                break

    async def handle_cleanup(self) -> None:
        await super().handle_cleanup()
        await self.disconnect()
        if self._supervisor_task:
            self._supervisor_task.cancel()
            await self._supervisor_task

    def handle_paradox_property_change(self, change: Any) -> None:
        from .paradoxport import ParadoxPort

        info = self._paradox.storage.data[change.type].get(change.key)
        if info and ("id" in info):
            id_ = info["id"]
            self.debug(
                "property change: %s[%s].%s: %s -> %s",
                change.type,
                id_,
                change.property,
                json_utils.dumps(change.old_value, extra_types=json_utils.EXTRA_TYPES_EXTENDED),
                json_utils.dumps(change.new_value, extra_types=json_utils.EXTRA_TYPES_EXTENDED),
            )
            obj = self._properties.setdefault(change.type, {}).setdefault(id_, {})
            obj[change.property] = change.new_value
            obj["label"] = info["label"]
        else:
            id_ = None
            self.debug(
                "property change: %s.%s: %s -> %s",
                change.type,
                change.property,
                json_utils.dumps(change.old_value, extra_types=json_utils.EXTRA_TYPES_EXTENDED),
                json_utils.dumps(change.new_value, extra_types=json_utils.EXTRA_TYPES_EXTENDED),
            )
            self._properties.setdefault(change.type, {})[change.property] = change.new_value

        for port in self.get_ports():
            pai_port = cast(ParadoxPort, port)

            try:
                pai_port.on_property_change(change.type, id_, change.property, change.old_value, change.new_value)
            except Exception as e:
                self.error("property change handler execution failed: %s", e, exc_info=True)

    def get_property(self, type_: str, id_: str | int | None, name: str) -> Property | None:
        if type_ == "system":
            return self._properties.get(type_, {}).get(name)
        else:
            return self._properties.get(type_, {}).get(id_, {}).get(name)

    def get_properties(self, type_: str, id_: str | int | None) -> dict[str, Property]:
        if type_ == "system":
            return self._properties.get(type_, {})
        else:
            return self._properties.get(type_, {}).get(id_, {})

    def _update_properties(self) -> None:
        changes = []

        for type_, properties in self._properties.items():
            type_info = self._paradox.storage.data.get(type_)
            if type_info is None:
                continue
            if isinstance(next(iter(self._properties[type_].values())), dict):  # properties with id
                for id_, props in properties.items():
                    id_info = type_info.get(id_)
                    if id_info is None:
                        continue
                    for prop, old_value in props.items():
                        new_value = id_info[prop]
                        if old_value != new_value:
                            changes.append(
                                SimpleNamespace(
                                    type=type_,
                                    key=id_,
                                    property=prop,
                                    old_value=old_value,
                                    new_value=new_value,
                                )
                            )
            else:
                # Flatten properties without id
                new_properties = {}
                for _, props in type_info.items():
                    new_properties.update(props)

                for prop, old_value in properties.items():
                    new_value = new_properties.get(prop)
                    if new_value is None:
                        continue
                    if old_value != new_value:
                        changes.append(
                            SimpleNamespace(
                                type=type_,
                                key=None,
                                property=prop,
                                old_value=old_value,
                                new_value=new_value,
                            )
                        )

            for change in changes:
                self.handle_paradox_property_change(change)

    async def set_area_armed_mode(self, area: int, armed_mode: str) -> None:
        self.debug("area %s: set armed mode to %s", area, armed_mode)
        if not await self._paradox.panel.control_partitions([area], armed_mode):
            raise exceptions.ParadoxCommandError("Failed to set area armed mode")

    async def set_zone_bypass(self, zone: int, bypass: bool) -> None:
        self.debug("zone %s: %s bypass", zone, ["clear", "set"][bypass])
        if not await self._paradox.panel.control_zones([zone], constants.ZONE_BYPASS_MAPPING[bypass]):
            raise exceptions.ParadoxCommandError("Failed to set zone bypass")

    async def set_output_action(self, output: int, action: str) -> None:
        self.debug("output %s: set action to %s", output, action)
        if not await self._paradox.panel.control_outputs([output], action):
            raise exceptions.ParadoxCommandError("Failed to set output action")
