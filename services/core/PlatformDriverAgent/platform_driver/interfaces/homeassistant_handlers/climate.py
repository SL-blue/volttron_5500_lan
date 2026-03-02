from __future__ import annotations
from typing import Any
from .base import BaseHandler

class ClimateHandler(BaseHandler):
    domain = "climate"

    # Mapping numeric mode values and HA hvac_mode strings
    _INT_TO_HVAC = {
        0: "off",
        2: "heat",
        3: "cool",
        4: "auto",
    }
    _HVAC_TO_INT = {v: k for k, v in _INT_TO_HVAC.items()}

    def set_point(self, register: Any, value: Any) -> None:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        if not entity_id.startswith("climate."):
            raise ValueError(f"ClimateHandler received non-climate entity_id: {entity_id}")

        if entity_point == "state":
            # Expect 0, 2, 3, or 4 for HVAC modes (off, heat, cool, auto)
            if not isinstance(value, int) or value not in self._INT_TO_HVAC:
                raise ValueError("Climate state should be an integer value of 0, 2, 3, or 4")

            hvac_mode = self._INT_TO_HVAC[value]
            payload = {"entity_id": entity_id, "hvac_mode": hvac_mode}
            self.driver._call_service(
                domain="climate",
                service="set_hvac_mode",
                payload=payload,
                op_desc=f"change mode of {entity_id} to {hvac_mode}",
            )
            return

        if entity_point == "temperature":
            # Accept int/float temperature
            if not isinstance(value, (int, float)):
                raise ValueError(f"Temperature must be int/float (got {value!r})")

            temp_to_send = value
            # if units == "C", convert Fahrenheit input to Celsius before sending to HA.
            if getattr(self.driver, "units", None) == "C":
                temp_to_send = round((float(value) - 32.0) * 5.0 / 9.0, 1)

            payload = {"entity_id": entity_id, "temperature": temp_to_send}
            self.driver._call_service(
                domain="climate",
                service="set_temperature",
                payload=payload,
                op_desc=f"set temperature of {entity_id} to {temp_to_send}",
            )
            return

        raise ValueError(
            f"Currently set_point is supported only for thermostats 'state' and 'temperature' ({entity_id})"
        )

    def scrape(self, register: Any) -> Any:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        entity_data = self.driver.get_entity_data(entity_id)

        if entity_point == "state":
            state = entity_data.get("state", None)
            if state in self._HVAC_TO_INT:
                return self._HVAC_TO_INT[state]
            raise ValueError(f"State {state!r} from {entity_id} is not yet supported")

        # Attributes (e.g., temperature, current_temperature, etc.)
        return entity_data.get("attributes", {}).get(entity_point, 0)