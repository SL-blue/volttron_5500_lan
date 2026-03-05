# homeassistant_handlers/lock.py
from __future__ import annotations

import logging
from typing import Any

from .base import BaseHandler

_log = logging.getLogger(__name__)


class LockHandler(BaseHandler):
    """
    Domain handler for Home Assistant `lock` entities.

    Value convention (consistent with other binary handlers):
        1 = locked   (HA state: "locked")
        0 = unlocked (HA state: "unlocked")

    Supported entity_point: "state"

    HA service mapping:
        value 1  ->  POST /api/services/lock/lock
        value 0  ->  POST /api/services/lock/unlock
    """

    domain = "lock"

    VALID_VALUES = {0, 1}

    # HA state string -> VOLTTRON int
    _STATE_MAP = {
        "locked":   1,
        "unlocked": 0,
    }

    # VOLTTRON int -> HA service name
    _SERVICE_MAP = {
        1: "lock",
        0: "unlock",
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
                f"Invalid lock value: {value}. Must be 0 (unlock) or 1 (lock)."
            )
        return v

    # ------------------------------------------------------------------
    # Write  (called by home_assistant.py  _set_point -> handler.set_point)
    # ------------------------------------------------------------------
    def set_point(self, register: Any, value: Any) -> None:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        if entity_point != "state":
            raise ValueError(
                f"Unsupported entity_point '{entity_point}' for lock domain. "
                f"Only 'state' is supported."
            )

        v = self._validate(value)
        service = self._SERVICE_MAP[v]
        payload = {"entity_id": entity_id}

        _log.info(
            f"LockHandler: calling lock.{service} on {entity_id}"
        )

        self.driver._call_service(
            domain=self.domain,
            service=service,
            payload=payload,
            op_desc=f"lock.{service} -> {entity_id}",
        )

    # ------------------------------------------------------------------
    # Read  (called by home_assistant.py  _scrape_all -> handler.scrape)
    # ------------------------------------------------------------------
    def scrape(self, register: Any) -> Any:
        entity_id = self._entity_id(register)
        entity_point = self._entity_point(register)

        entity_data = self.driver.get_entity_data(entity_id)

        if entity_point == "state":
            raw_state = entity_data.get("state", None)
            mapped = self._STATE_MAP.get(raw_state)

            if mapped is None:
                _log.warning(
                    f"LockHandler: unexpected state '{raw_state}' for {entity_id}. "
                    f"Returning raw value."
                )
                return raw_state

            return mapped

        # For any other attribute (e.g. "friendly_name"), return it directly
        return entity_data.get("attributes", {}).get(entity_point, None)