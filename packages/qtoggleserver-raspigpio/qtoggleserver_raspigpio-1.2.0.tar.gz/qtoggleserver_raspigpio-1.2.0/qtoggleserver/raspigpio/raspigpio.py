import subprocess

from qtoggleserver.core import ports as core_ports
from qtoggleserver.utils import json as json_utils


class GPIO(core_ports.Port):
    TYPE = core_ports.TYPE_BOOLEAN

    ADDITIONAL_ATTRDEFS = {
        "output": {
            "display_name": "Is Output",
            "description": "Controls the port direction.",
            "type": "boolean",
            "modifiable": True,
        },
        "pull": {
            "display_name": "Pull Mode",
            "description": "Configures port's pull resistors.",
            "type": "string",
            "modifiable": True,
            "choices": [
                {"value": "off", "display_name": "Off"},
                {"value": "up", "display_name": "Pull-up"},
                {"value": "down", "display_name": "Pull-down"},
            ],
        },
    }

    _PULL_MAPPING = {
        None: "n",
        False: "d",
        True: "u",
    }

    _PULL_VALUE_MAPPING = {
        None: "off",
        True: "up",
        False: "down",
        "off": None,
        "up": True,
        "down": False,
    }

    _OUTPUT_LEVEL_MAPPING = {
        False: "l",
        True: "h",
    }

    def __init__(self, no: int, def_value: bool | None = None, def_output: bool | None = None) -> None:
        self._no: int = no
        self._def_value: bool | None = def_value  # also plays the role of pull setup

        # The default i/o state
        if def_output is None:
            def_output = "func=OUTPUT" in self._exec_raspi_gpio(f"get {self._no}")

        self._def_output: bool = def_output

        super().__init__(port_id=f"gpio{no}")

    async def handle_enable(self) -> None:
        self._configure(self._def_output, self._def_value)

    async def read_value(self) -> bool:
        return "level=1" in self._exec_raspi_gpio(f"get {self._no}")

    @core_ports.skip_write_unavailable
    async def write_value(self, value: bool) -> None:
        self.debug("writing output value %s", json_utils.dumps(value))
        self._exec_raspi_gpio(f"set {self._no} d{self._OUTPUT_LEVEL_MAPPING[value]}")

    async def attr_is_writable(self) -> bool:
        return await self.attr_is_output()

    async def attr_set_output(self, output: bool) -> None:
        if not self.is_enabled():
            self._def_output = output
            return

        self._configure(output, self._def_value)

    async def attr_is_output(self) -> bool:
        return "func=OUTPUT" in self._exec_raspi_gpio(f"get {self._no}")

    async def attr_get_pull(self) -> str:
        return self._PULL_VALUE_MAPPING[self._def_value]

    async def attr_set_pull(self, pull: str) -> None:
        self._def_value = self._PULL_VALUE_MAPPING[pull]
        if self.is_enabled() and not await self.attr_is_output():
            self._configure(output=False, def_value=self._def_value)

    def _configure(self, output: bool, def_value: bool | None) -> None:
        if output:
            def_value = def_value or False  # def_value can be None
            self.debug("configuring as output (initial=%s)", str(def_value).lower())
            self._exec_raspi_gpio(f"set {self._no} op pn d{self._OUTPUT_LEVEL_MAPPING[def_value]}")
        else:
            self.debug("configuring as input (pull=%s)", self._PULL_VALUE_MAPPING[def_value])
            self._exec_raspi_gpio(f"set {self._no} ip p{self._PULL_MAPPING[def_value]}")

    def _exec_raspi_gpio(self, params: str) -> str:
        cmd = ["raspi-gpio"] + params.split()
        return subprocess.check_output(cmd).decode().strip()
