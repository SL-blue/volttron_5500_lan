from __future__ import annotations

from typing import Any

from .base import BaseHandler


class InputBooleanHandler(BaseHandler):
    domain = "input_boolean"

    def set_point(self, register: Any, value: Any) -> None:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        if not entity_id.startswith("input_boolean."):
            raise ValueError(f"InputBooleanHandler received non-input_boolean entity_id: {entity_id}")

        # Design: only state is writable for input_boolean
        if entity_point != "state":
            raise ValueError("Currently, input_booleans only support setting 'state'")

        v01 = self._normalize_on_off_to_int01(value)
        if v01 is None:
            raise ValueError(f"State value for {entity_id} must be 0/1 or 'on'/'off' (got {value!r})")

        service = "turn_on" if v01 == 1 else "turn_off"
        payload = {"entity_id": entity_id}

        # Uses Interface._call_service() from home_assistant.py
        self.driver._call_service(
            domain="input_boolean",
            service=service,
            payload=payload,
            op_desc=f"set {entity_id} {service}",
        )

    def scrape(self, register: Any) -> Any:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        entity_data = self.driver.get_entity_data(entity_id)

        if entity_point == "state":
            state = entity_data.get("state", None)
            v01 = self._normalize_on_off_to_int01(state)
            # If HA returns something unexpected, keep it explicit (None) rather than lying.
            if v01 is None:
                raise ValueError(f"Unsupported input_boolean state for {entity_id}: {state!r}")
            return v01

        # For non-state points (attributes), return attribute value or 0 if missing.
        return entity_data.get("attributes", {}).get(entity_point, 0)