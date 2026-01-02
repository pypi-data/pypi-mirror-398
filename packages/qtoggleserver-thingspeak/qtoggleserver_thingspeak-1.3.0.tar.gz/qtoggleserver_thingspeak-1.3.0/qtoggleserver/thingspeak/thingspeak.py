import asyncio
import logging
import time

from datetime import datetime, timezone

import aiohttp
import pytz

from qtoggleserver.core import events as core_events
from qtoggleserver.core import ports as core_ports
from qtoggleserver.core.typing import Attributes, NullablePortValue
from qtoggleserver.lib.filtereventhandler import FilterEventHandler

from .exceptions import ThingSpeakException


logger = logging.getLogger(__name__)


class ThingSpeakEventHandler(FilterEventHandler):
    BASE_URL = "https://api.thingspeak.com"
    UPDATE_ENDPOINT = "/update.json"
    MAX_FIELDS = 8

    logger = logger

    def __init__(
        self,
        *,
        api_key: str,
        fields: dict[str, int],
        period: int | None = None,
        min_period: int | None = None,
        **kwargs,
    ) -> None:
        if None not in (period, min_period):
            raise ThingSpeakException("Parameters period and min_period cannot be both specified")

        if period is min_period is None:
            raise ThingSpeakException("Either period or min_period must be specified")

        self._api_key: str = api_key
        self._fields: dict[str, int] = fields
        self._period: int | None = period
        self._min_period: int | None = min_period

        self._last_send_time: float = time.time()
        self._values_cache: dict[int, NullablePortValue] = {}

        # Start periodic send task
        if self._period is not None:
            self._periodic_send_values_task = asyncio.create_task(self.periodic_send_values())

        super().__init__(**kwargs)

    async def on_value_change(
        self,
        event: core_events.Event,
        port: core_ports.BasePort,
        old_value: NullablePortValue,
        new_value: NullablePortValue,
        attrs: Attributes,
    ) -> None:
        # When period is specified, periodic_send_values() will take care of sending values
        if self._period is not None:
            return

        # Look up port id -> field number mapping; if not present, values for this port are not configured for sending
        field_no = self._fields.get(port.get_id())
        if field_no is None:
            return

        self._values_cache[field_no] = new_value

        # Don't send samples more often than min_period
        now = time.time()
        if now - self._last_send_time < self._min_period:
            return

        self._last_send_time = now
        created_at = datetime.fromtimestamp(event.get_timestamp(), tz=pytz.UTC)

        try:
            await self.send_values(self._values_cache, created_at)
        except Exception as e:
            self.error("sending values failed: %s", e, exc_info=True)

        self._values_cache = {}

    async def send_values(self, values: dict[int, float], created_at: datetime) -> None:
        if not values:
            raise ThingSpeakException("Refusing to send empty values")

        url = self.BASE_URL + self.UPDATE_ENDPOINT
        data = {"api_key": self._api_key, "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")}

        # Add field values
        data.update({f"field{no}": value for no, value in values.items()})

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(url, json=data) as response:
                await response.json()

        field_msgs = []
        for i in range(1, self.MAX_FIELDS + 1):
            if i in values:
                field_msgs.append(f"field{i}={values[i]}")

        self.debug("sent %s at %s", ", ".join(field_msgs), data["created_at"])

    async def periodic_send_values(self) -> None:
        while True:
            ports = [core_ports.get(port_id) for port_id in self._fields.keys()]
            port_values = {p.get_id(): p.get_last_read_value() for p in ports}
            field_values = {self._fields[id_]: value for id_, value in port_values.items()}

            try:
                if field_values:
                    await self.send_values(field_values, datetime.now(timezone.utc))
                else:
                    self.debug("not sending empty values")
            except asyncio.CancelledError:
                self.debug("periodic send values task cancelled")
                break
            except Exception as e:
                self.error("sending values failed: %s", e, exc_info=True)

            await asyncio.sleep(self._period)
