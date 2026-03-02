# homeassistant_handlers/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseHandler(ABC):
    """
    Base contract for domain handlers.

    Interface alignment:
      - home_assistant.py calls:
          handler.set_point(register=register, value=register.value)
          value = handler.scrape(register=register)
    """
    domain: str  # e.g. "light", "input_boolean", etc.

    def __init__(self, driver: Any):
        self.driver = driver

    @abstractmethod
    def set_point(self, register: Any, value: Any) -> None:
        """Validate + perform HA service calls. Should raise ValueError on invalid input."""
        raise NotImplementedError

    @abstractmethod
    def scrape(self, register: Any) -> Any:
        """Read HA state/attributes and return the VOLTTRON value for this register."""
        raise NotImplementedError

    def _entity_id(self, register: Any) -> str:
        return getattr(register, "entity_id", "")

    def _entity_point(self, register: Any) -> str:
        return getattr(register, "entity_point", "")

    def _normalize_on_off_to_int01(self, state: Any) -> Optional[int]:
        """
        Convert HA-style 'on'/'off' (or bool/int variants) to 1/0.
        Returns None if state is not recognized.
        """
        if state is None:
            return None
        if isinstance(state, bool):
            return 1 if state else 0
        if isinstance(state, int):
            if state in (0, 1):
                return state
            return None
        if isinstance(state, str):
            s = state.strip().lower()
            if s in ("on", "true", "1"):
                return 1
            if s in ("off", "false", "0"):
                return 0
        return None