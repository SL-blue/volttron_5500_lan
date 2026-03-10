# tests/homeassistant/unit/test_climate_handler_unit.py
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from platform_driver.interfaces.homeassistant_handlers.climate import ClimateHandler


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _make_register(entity_id="climate.living_room", entity_point="temperature"):
    reg = MagicMock()
    reg.entity_id = entity_id
    reg.entity_point = entity_point
    return reg


def _make_handler():
    driver = MagicMock()
    handler = ClimateHandler(driver)
    return handler, driver


# ==================================================================
# Validation tests
# ==================================================================
class TestClimateValidation:

    def test_valid_temperature_int(self):
        h, _ = _make_handler()
        assert h._validate_temperature(22) == 22.0

    def test_valid_temperature_float(self):
        h, _ = _make_handler()
        assert h._validate_temperature(22.5) == 22.5

    def test_valid_temperature_string_numeric(self):
        h, _ = _make_handler()
        assert h._validate_temperature("23") == 23.0

    def test_invalid_temperature_string_raises(self):
        h, _ = _make_handler()
        with pytest.raises(ValueError, match="Invalid temperature value"):
            h._validate_temperature("hot")

    def test_valid_hvac_mode(self):
        h, _ = _make_handler()
        for mode in ["heat", "cool", "auto", "off", "heat_cool", "dry", "fan_only"]:
            assert h._validate_hvac_mode(mode) == mode

    def test_valid_hvac_mode_case_insensitive(self):
        h, _ = _make_handler()
        assert h._validate_hvac_mode("HEAT") == "heat"
        assert h._validate_hvac_mode("Cool") == "cool"

    def test_invalid_hvac_mode_raises(self):
        h, _ = _make_handler()
        with pytest.raises(ValueError, match="Invalid HVAC mode"):
            h._validate_hvac_mode("turbo")


# ==================================================================
# set_point tests
# ==================================================================
class TestClimateSetPoint:

    def test_set_temperature(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="temperature")

        h.set_point(register=reg, value=23.5)

        driver._call_service.assert_called_once_with(
            domain="climate",
            service="set_temperature",
            payload={"entity_id": "climate.living_room", "temperature": 23.5},
            op_desc="climate.set_temperature (23.5) -> climate.living_room",
        )

    def test_set_hvac_mode(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="hvac_mode")

        h.set_point(register=reg, value="cool")

        driver._call_service.assert_called_once_with(
            domain="climate",
            service="set_hvac_mode",
            payload={"entity_id": "climate.living_room", "hvac_mode": "cool"},
            op_desc="climate.set_hvac_mode (cool) -> climate.living_room",
        )

    def test_invalid_temperature_raises(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="temperature")

        with pytest.raises(ValueError, match="Invalid temperature value"):
            h.set_point(register=reg, value="warm")

        driver._call_service.assert_not_called()

    def test_invalid_hvac_mode_raises(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="hvac_mode")

        with pytest.raises(ValueError, match="Invalid HVAC mode"):
            h.set_point(register=reg, value="turbo")

        driver._call_service.assert_not_called()

    def test_unsupported_entity_point_raises(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="fan_speed")

        with pytest.raises(ValueError, match="Unsupported entity_point"):
            h.set_point(register=reg, value=1)

        driver._call_service.assert_not_called()


# ==================================================================
# scrape tests
# ==================================================================
class TestClimateScrape:

    def test_scrape_state_returns_hvac_mode(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="state")
        driver.get_entity_data.return_value = {
            "state": "heat",
            "attributes": {"temperature": 22},
        }

        result = h.scrape(register=reg)

        assert result == "heat"
        driver.get_entity_data.assert_called_once_with("climate.living_room")

    def test_scrape_temperature_returns_value(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="temperature")
        driver.get_entity_data.return_value = {
            "state": "heat",
            "attributes": {"temperature": 22.5},
        }

        result = h.scrape(register=reg)

        assert result == 22.5

    def test_scrape_current_temperature(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="current_temperature")
        driver.get_entity_data.return_value = {
            "state": "cool",
            "attributes": {"current_temperature": 25.0},
        }

        result = h.scrape(register=reg)

        assert result == 25.0

    def test_scrape_missing_attribute_returns_none(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="humidity")
        driver.get_entity_data.return_value = {
            "state": "off",
            "attributes": {},
        }

        result = h.scrape(register=reg)

        assert result is None