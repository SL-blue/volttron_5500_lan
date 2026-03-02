from __future__ import annotations
from typing import Any
from .base import BaseHandler

class LightHandler(BaseHandler):
    domain = "light"

    def set_point(self, register: Any, value: Any) -> None:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        if not entity_id.startswith("light."):
            raise ValueError(f"LightHandler received non-light entity_id: {entity_id}")

        # Turn on/off lights
        if entity_point == "state":
            v01 = self._normalize_on_off_to_int01(value)
            if v01 is None:
                raise ValueError(f"State value for {entity_id} must be 0/1 or 'on'/'off' (got {value!r})")

            service = "turn_on" if v01 == 1 else "turn_off"
            payload = {"entity_id": entity_id}
            self.driver._call_service(
                domain="light",
                service=service,
                payload=payload,
                op_desc=f"{service} {entity_id}",
            )
            return

        # Set brightness (0-255)
        if entity_point == "brightness":
            if not isinstance(value, int) or not (0 <= value <= 255):
                raise ValueError("Brightness value should be an integer between 0 and 255")

            # In HA, brightness is set via light.turn_on with brightness field
            payload = {"entity_id": entity_id, "brightness": value}
            self.driver._call_service(
                domain="light",
                service="turn_on",
                payload=payload,
                op_desc=f"set brightness of {entity_id} to {value}",
            )
            return

        raise ValueError(f"Unexpected point_name {register.point_name} for register {entity_id}")

    def scrape(self, register: Any) -> Any:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        entity_data = self.driver.get_entity_data(entity_id)

        if entity_point == "state":
            state = entity_data.get("state", None)
            v01 = self._normalize_on_off_to_int01(state)
            if v01 is None:
                raise ValueError(f"Unsupported light state for {entity_id}: {state!r}")
            return v01

        # Attributes (e.g., brightness, color_temp, etc.)
        return entity_data.get("attributes", {}).get(entity_point, 0)