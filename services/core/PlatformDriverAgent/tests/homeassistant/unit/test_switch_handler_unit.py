# tests/homeassistant/unit/test_switch_handler_unit.py
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from platform_driver.interfaces.homeassistant_handlers.switch import SwitchHandler


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _make_register(entity_id="switch.kitchen_light", entity_point="state"):
    reg = MagicMock()
    reg.entity_id = entity_id
    reg.entity_point = entity_point
    return reg


def _make_handler():
    driver = MagicMock()
    handler = SwitchHandler(driver)
    return handler, driver


# ==================================================================
# Validation tests
# ==================================================================
class TestSwitchValidation:

    def test_valid_value_1(self):
        h, _ = _make_handler()
        assert h._validate(1) == 1

    def test_valid_value_0(self):
        h, _ = _make_handler()
        assert h._validate(0) == 0

    def test_invalid_value_raises(self):
        h, _ = _make_handler()
        with pytest.raises(ValueError, match="Invalid switch value"):
            h._validate(2)

    def test_string_castable_to_valid_int(self):
        h, _ = _make_handler()
        assert h._validate("0") == 0

    def test_string_non_numeric_raises(self):
        h, _ = _make_handler()
        with pytest.raises((ValueError, TypeError)):
            h._validate("abc")


# ==================================================================
# set_point tests
# ==================================================================
class TestSwitchSetPoint:

    def test_turn_on_calls_turn_on_service(self):
        h, driver = _make_handler()
        reg = _make_register()

        h.set_point(register=reg, value=1)

        driver._call_service.assert_called_once_with(
            domain="switch",
            service="turn_on",
            payload={"entity_id": "switch.kitchen_light"},
            op_desc="switch.turn_on -> switch.kitchen_light",
        )

    def test_turn_off_calls_turn_off_service(self):
        h, driver = _make_handler()
        reg = _make_register()

        h.set_point(register=reg, value=0)

        driver._call_service.assert_called_once_with(
            domain="switch",
            service="turn_off",
            payload={"entity_id": "switch.kitchen_light"},
            op_desc="switch.turn_off -> switch.kitchen_light",
        )

    def test_invalid_value_raises(self):
        h, driver = _make_handler()
        reg = _make_register()

        with pytest.raises(ValueError, match="Invalid switch value"):
            h.set_point(register=reg, value=99)

        driver._call_service.assert_not_called()

    def test_unsupported_entity_point_raises(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="brightness")

        with pytest.raises(ValueError, match="Unsupported entity_point"):
            h.set_point(register=reg, value=1)

        driver._call_service.assert_not_called()


# ==================================================================
# scrape tests
# ==================================================================
class TestSwitchScrape:

    def test_scrape_on_returns_1(self):
        h, driver = _make_handler()
        reg = _make_register()
        driver.get_entity_data.return_value = {"state": "on", "attributes": {}}

        result = h.scrape(register=reg)

        assert result == 1
        driver.get_entity_data.assert_called_once_with("switch.kitchen_light")

    def test_scrape_off_returns_0(self):
        h, driver = _make_handler()
        reg = _make_register()
        driver.get_entity_data.return_value = {"state": "off", "attributes": {}}

        result = h.scrape(register=reg)

        assert result == 0

    def test_scrape_attribute_returns_attribute_value(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="friendly_name")
        driver.get_entity_data.return_value = {
            "state": "on",
            "attributes": {"friendly_name": "Kitchen Light"},
        }

        result = h.scrape(register=reg)

        assert result == "Kitchen Light"

    def test_scrape_unavailable_returns_none(self):
        h, driver = _make_handler()
        reg = _make_register()
        driver.get_entity_data.return_value = {"state": "unavailable", "attributes": {}}

        result = h.scrape(register=reg)

        # "unavailable" is not in on/off map, _normalize_on_off_to_int01 returns None
        assert result is None