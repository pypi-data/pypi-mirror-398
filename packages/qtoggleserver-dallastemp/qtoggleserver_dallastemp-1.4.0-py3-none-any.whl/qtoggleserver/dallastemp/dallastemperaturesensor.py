import logging
import re

from qtoggleserver.core import ports as core_ports
from qtoggleserver.lib import onewire


class DallasTemperatureSensor(onewire.OneWirePeripheral):
    TEMP_PATTERN = r"t=(\d+)"
    ERROR_VALUE = "85000"  # indicates a communication error

    logger = logging.getLogger(__name__)

    def __init__(self, **kwargs) -> None:
        self._temp: float | None = None

        super().__init__(**kwargs)

    async def make_port_args(self) -> list[type[core_ports.BasePort]]:
        from .ports import Temperature

        return [Temperature]

    def get_temp(self) -> float | None:
        data = self.read()
        if data:
            m = re.search(self.TEMP_PATTERN, data, re.MULTILINE | re.DOTALL)
            if m:
                value_str = m.group(1)
                if value_str == self.ERROR_VALUE:
                    raise core_ports.PortReadError("Sensor communication error")

                self._temp = round(int(value_str) / 100.0) / 10.0
                self.debug("temperature is %.1f degrees", self._temp)

        return self._temp
