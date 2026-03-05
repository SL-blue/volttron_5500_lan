# tests/homeassistant/unit/test_light_handler_unit.py
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from platform_driver.interfaces.homeassistant_handlers.light import LightHandler


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _make_register(entity_id="light.living_room", entity_point="state"):
    reg = MagicMock()
    reg.entity_id = entity_id
    reg.entity_point = entity_point
    return reg


def _make_handler():
    driver = MagicMock()
    handler = LightHandler(driver)
    return handler, driver


# ==================================================================
# Validation tests
# ==================================================================
class TestLightValidation:

    def test_valid_state_1(self):
        h, _ = _make_handler()
        assert h._validate_state(1) == 1

    def test_valid_state_0(self):
        h, _ = _make_handler()
        assert h._validate_state(0) == 0

    def test_invalid_state_raises(self):
        h, _ = _make_handler()
        with pytest.raises(ValueError, match="Invalid light state value"):
            h._validate_state(2)

    def test_valid_brightness_0(self):
        h, _ = _make_handler()
        assert h._validate_brightness(0) == 0

    def test_valid_brightness_255(self):
        h, _ = _make_handler()
        assert h._validate_brightness(255) == 255

    def test_valid_brightness_middle(self):
        h, _ = _make_handler()
        assert h._validate_brightness(128) == 128

    def test_invalid_brightness_too_high(self):
        h, _ = _make_handler()
        with pytest.raises(ValueError, match="Invalid brightness value"):
            h._validate_brightness(256)

    def test_invalid_brightness_negative(self):
        h, _ = _make_handler()
        with pytest.raises(ValueError, match="Invalid brightness value"):
            h._validate_brightness(-1)


# ==================================================================
# set_point tests
# ==================================================================
class TestLightSetPoint:

    def test_turn_on_calls_turn_on_service(self):
        h, driver = _make_handler()
        reg = _make_register()

        h.set_point(register=reg, value=1)

        driver._call_service.assert_called_once_with(
            domain="light",
            service="turn_on",
            payload={"entity_id": "light.living_room"},
            op_desc="light.turn_on -> light.living_room",
        )

    def test_turn_off_calls_turn_off_service(self):
        h, driver = _make_handler()
        reg = _make_register()

        h.set_point(register=reg, value=0)

        driver._call_service.assert_called_once_with(
            domain="light",
            service="turn_off",
            payload={"entity_id": "light.living_room"},
            op_desc="light.turn_off -> light.living_room",
        )

    def test_set_brightness(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="brightness")

        h.set_point(register=reg, value=200)

        driver._call_service.assert_called_once_with(
            domain="light",
            service="turn_on",
            payload={"entity_id": "light.living_room", "brightness": 200},
            op_desc="light.turn_on (brightness=200) -> light.living_room",
        )

    def test_invalid_state_raises(self):
        h, driver = _make_handler()
        reg = _make_register()

        with pytest.raises(ValueError, match="Invalid light state value"):
            h.set_point(register=reg, value=5)

        driver._call_service.assert_not_called()

    def test_invalid_brightness_raises(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="brightness")

        with pytest.raises(ValueError, match="Invalid brightness value"):
            h.set_point(register=reg, value=300)

        driver._call_service.assert_not_called()

    def test_unsupported_entity_point_raises(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="color_temp")

        with pytest.raises(ValueError, match="Unsupported entity_point"):
            h.set_point(register=reg, value=100)

        driver._call_service.assert_not_called()


# ==================================================================
# scrape tests
# ==================================================================
class TestLightScrape:

    def test_scrape_on_returns_1(self):
        h, driver = _make_handler()
        reg = _make_register()
        driver.get_entity_data.return_value = {"state": "on", "attributes": {}}

        result = h.scrape(register=reg)

        assert result == 1
        driver.get_entity_data.assert_called_once_with("light.living_room")

    def test_scrape_off_returns_0(self):
        h, driver = _make_handler()
        reg = _make_register()
        driver.get_entity_data.return_value = {"state": "off", "attributes": {}}

        result = h.scrape(register=reg)

        assert result == 0

    def test_scrape_brightness_returns_value(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="brightness")
        driver.get_entity_data.return_value = {
            "state": "on",
            "attributes": {"brightness": 180},
        }

        result = h.scrape(register=reg)

        assert result == 180

    def test_scrape_missing_attribute_returns_0(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="brightness")
        driver.get_entity_data.return_value = {
            "state": "off",
            "attributes": {},
        }

        result = h.scrape(register=reg)

        assert result == 0