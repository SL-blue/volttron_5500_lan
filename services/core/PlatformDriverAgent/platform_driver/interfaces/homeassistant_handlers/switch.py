# homeassistant_handlers/switch.py
from __future__ import annotations

import logging
from typing import Any

from .base import BaseHandler

_log = logging.getLogger(__name__)


class SwitchHandler(BaseHandler):
    """
    Domain handler for Home Assistant `switch` entities.

    Value convention:
        1 = on   (HA state: "on")
        0 = off  (HA state: "off")

    Supported entity_point: "state"

    HA service mapping:
        value 1  ->  POST /api/services/switch/turn_on
        value 0  ->  POST /api/services/switch/turn_off
    """

    domain = "switch"

    VALID_VALUES = {0, 1}

    # VOLTTRON int -> HA service name
    _SERVICE_MAP = {
        1: "turn_on",
        0: "turn_off",
    }

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate(self, value: Any) -> int:
        """
        Ensure *value* is 0 or 1.  Returns the validated int.
        Raises ValueError for anything else.
        """
        v = int(value)
        if v not in self.VALID_VALUES:
            raise ValueError(
                f"Invalid switch value: {value}. Must be 0 (off) or 1 (on)."
            )
        return v

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def set_point(self, register: Any, value: Any) -> None:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        if entity_point != "state":
            raise ValueError(
                f"Unsupported entity_point '{entity_point}' for switch domain. "
                f"Only 'state' is supported."
            )

        v = self._validate(value)
        service = self._SERVICE_MAP[v]
        payload = {"entity_id": entity_id}

        _log.info(
            f"SwitchHandler: calling switch.{service} on {entity_id}"
        )

        self.driver._call_service(
            domain=self.domain,
            service=service,
            payload=payload,
            op_desc=f"switch.{service} -> {entity_id}",
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

        # For any other attribute, return it directly
        return entity_data.get("attributes", {}).get(entity_point, None)