import logging

from typing import cast

from qtoggleserver.lib import onewire

from .dallastemperaturesensor import DallasTemperatureSensor


logger = logging.getLogger(__name__)


class Temperature(onewire.OneWirePort):
    TYPE = "number"
    WRITABLE = False
    MIN = -55
    MAX = 125
    UNIT = "\xb0C"  # degrees celsius

    ID = "temperature"

    async def read_value(self) -> float | None:
        return cast(DallasTemperatureSensor, self.get_peripheral()).get_temp()
