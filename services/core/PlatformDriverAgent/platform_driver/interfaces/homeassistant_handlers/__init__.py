# homeassistant_handlers/__init__.py
from __future__ import annotations

from typing import Dict

from .base import BaseHandler
from .input_boolean import InputBooleanHandler
from .light import LightHandler
from .climate import ClimateHandler
from .lock import LockHandler
from .switch import SwitchHandler

HANDLERS = {
    "input_boolean": InputBooleanHandler,
    "light": LightHandler,
    "climate": ClimateHandler,
    "lock": LockHandler,
    "switch": SwitchHandler,
}


def get_default_handlers(driver) -> Dict[str, BaseHandler]:
    """
    Called by home_assistant.py configure():
        self._handlers = get_default_handlers(self)

    Returns domain -> handler instance.
    """
    return {domain: handler_cls(driver) for domain, handler_cls in HANDLERS.items()}