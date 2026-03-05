# homeassistant_handlers/climate.py
from __future__ import annotations

import logging
from typing import Any

from .base import BaseHandler

_log = logging.getLogger(__name__)


class ClimateHandler(BaseHandler):
    """
    Domain handler for Home Assistant `climate` entities.

    Supported entity_points:
        - "state"            : read current HVAC mode (read-only via scrape)
        - "temperature"      : set target temperature
        - "hvac_mode"        : set HVAC mode (heat, cool, auto, off, etc.)

    HA service mapping:
        temperature=<n>      ->  POST /api/services/climate/set_temperature
        hvac_mode=<mode>     ->  POST /api/services/climate/set_hvac_mode
    """

    domain = "climate"

    VALID_HVAC_MODES = {"heat", "cool", "auto", "off", "heat_cool", "dry", "fan_only"}

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate_temperature(self, value: Any) -> float:
        try:
            v = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid temperature value: {value}. Must be numeric."
            )
        return v

    def _validate_hvac_mode(self, value: Any) -> str:
        mode = str(value).strip().lower()
        if mode not in self.VALID_HVAC_MODES:
            raise ValueError(
                f"Invalid HVAC mode: '{value}'. "
                f"Supported modes: {', '.join(sorted(self.VALID_HVAC_MODES))}"
            )
        return mode

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def set_point(self, register: Any, value: Any) -> None:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        if entity_point == "temperature":
            v = self._validate_temperature(value)
            payload = {"entity_id": entity_id, "temperature": v}

            _log.info(
                f"ClimateHandler: setting temperature={v} on {entity_id}"
            )

            self.driver._call_service(
                domain=self.domain,
                service="set_temperature",
                payload=payload,
                op_desc=f"climate.set_temperature ({v}) -> {entity_id}",
            )

        elif entity_point == "hvac_mode":
            mode = self._validate_hvac_mode(value)
            payload = {"entity_id": entity_id, "hvac_mode": mode}

            _log.info(
                f"ClimateHandler: setting hvac_mode={mode} on {entity_id}"
            )

            self.driver._call_service(
                domain=self.domain,
                service="set_hvac_mode",
                payload=payload,
                op_desc=f"climate.set_hvac_mode ({mode}) -> {entity_id}",
            )

        else:
            raise ValueError(
                f"Unsupported entity_point '{entity_point}' for climate domain. "
                f"Supported: 'temperature', 'hvac_mode'."
            )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def scrape(self, register: Any) -> Any:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        entity_data = self.driver.get_entity_data(entity_id)

        if entity_point == "state":
            # HA climate state is the current HVAC mode string (e.g. "heat", "cool", "off")
            return entity_data.get("state", None)

        # For attributes like "temperature", "current_temperature", "hvac_mode", etc.
        return entity_data.get("attributes", {}).get(entity_point, None)