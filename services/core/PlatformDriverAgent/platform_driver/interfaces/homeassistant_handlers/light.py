# homeassistant_handlers/light.py
from __future__ import annotations

import logging
from typing import Any

from .base import BaseHandler

_log = logging.getLogger(__name__)


class LightHandler(BaseHandler):
    """
    Domain handler for Home Assistant `light` entities.

    Value convention for 'state' entity_point:
        1 = on   (HA state: "on")
        0 = off  (HA state: "off")

    Supported entity_points:
        - "state"       : turn_on / turn_off  (value must be 0 or 1)
        - "brightness"  : turn_on with brightness attribute (value 0-255)

    HA service mapping:
        state=1          ->  POST /api/services/light/turn_on
        state=0          ->  POST /api/services/light/turn_off
        brightness=<n>   ->  POST /api/services/light/turn_on  {"brightness": n}
    """

    domain = "light"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate_state(self, value: Any) -> int:
        v = int(value)
        if v not in (0, 1):
            raise ValueError(
                f"Invalid light state value: {value}. Must be 0 (off) or 1 (on)."
            )
        return v

    def _validate_brightness(self, value: Any) -> int:
        v = int(value)
        if not (0 <= v <= 255):
            raise ValueError(
                f"Invalid brightness value: {value}. Must be between 0 and 255."
            )
        return v

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def set_point(self, register: Any, value: Any) -> None:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        if entity_point == "state":
            v = self._validate_state(value)
            if v == 1:
                service = "turn_on"
            else:
                service = "turn_off"
            payload = {"entity_id": entity_id}

            _log.info(f"LightHandler: calling light.{service} on {entity_id}")

            self.driver._call_service(
                domain=self.domain,
                service=service,
                payload=payload,
                op_desc=f"light.{service} -> {entity_id}",
            )

        elif entity_point == "brightness":
            v = self._validate_brightness(value)
            payload = {"entity_id": entity_id, "brightness": v}

            _log.info(
                f"LightHandler: setting brightness={v} on {entity_id}"
            )

            self.driver._call_service(
                domain=self.domain,
                service="turn_on",
                payload=payload,
                op_desc=f"light.turn_on (brightness={v}) -> {entity_id}",
            )

        else:
            raise ValueError(
                f"Unsupported entity_point '{entity_point}' for light domain. "
                f"Supported: 'state', 'brightness'."
            )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def scrape(self, register: Any) -> Any:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        entity_data = self.driver.get_entity_data(entity_id)

        if entity_point == "state":
            raw_state = entity_data.get("state", None)
            return self._normalize_on_off_to_int01(raw_state)

        # For attributes like "brightness", "color_temp", etc.
        return entity_data.get("attributes", {}).get(entity_point, 0)