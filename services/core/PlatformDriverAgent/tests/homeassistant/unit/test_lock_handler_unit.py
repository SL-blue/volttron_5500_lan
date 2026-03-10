# tests/homeassistant/unit/test_lock_handler_unit.py
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, call

from platform_driver.interfaces.homeassistant_handlers.lock import LockHandler


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _make_register(entity_id="lock.front_door", entity_point="state"):
    reg = MagicMock()
    reg.entity_id = entity_id
    reg.entity_point = entity_point
    return reg


def _make_handler():
    driver = MagicMock()
    handler = LockHandler(driver)
    return handler, driver


# ==================================================================
# Validation tests
# ==================================================================
class TestLockValidation:

    def test_valid_value_1(self):
        h, _ = _make_handler()
        assert h._validate(1) == 1

    def test_valid_value_0(self):
        h, _ = _make_handler()
        assert h._validate(0) == 0

    def test_invalid_value_raises(self):
        h, _ = _make_handler()
        with pytest.raises(ValueError, match="Invalid lock value"):
            h._validate(3)

    def test_invalid_negative_raises(self):
        h, _ = _make_handler()
        with pytest.raises(ValueError, match="Invalid lock value"):
            h._validate(-1)

    def test_string_castable_to_valid_int(self):
        """Value '1' (string) should be cast to int and accepted."""
        h, _ = _make_handler()
        assert h._validate("1") == 1

    def test_string_non_numeric_raises(self):
        h, _ = _make_handler()
        with pytest.raises((ValueError, TypeError)):
            h._validate("abc")


# ==================================================================
# set_point tests
# ==================================================================
class TestLockSetPoint:

    def test_lock_calls_lock_service(self):
        h, driver = _make_handler()
        reg = _make_register()

        h.set_point(register=reg, value=1)

        driver._call_service.assert_called_once_with(
            domain="lock",
            service="lock",
            payload={"entity_id": "lock.front_door"},
            op_desc="lock.lock -> lock.front_door",
        )

    def test_unlock_calls_unlock_service(self):
        h, driver = _make_handler()
        reg = _make_register()

        h.set_point(register=reg, value=0)

        driver._call_service.assert_called_once_with(
            domain="lock",
            service="unlock",
            payload={"entity_id": "lock.front_door"},
            op_desc="lock.unlock -> lock.front_door",
        )

    def test_invalid_value_raises(self):
        h, driver = _make_handler()
        reg = _make_register()

        with pytest.raises(ValueError, match="Invalid lock value"):
            h.set_point(register=reg, value=5)

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
class TestLockScrape:

    def test_scrape_locked_returns_1(self):
        h, driver = _make_handler()
        reg = _make_register()
        driver.get_entity_data.return_value = {"state": "locked", "attributes": {}}

        result = h.scrape(register=reg)

        assert result == 1
        driver.get_entity_data.assert_called_once_with("lock.front_door")

    def test_scrape_unlocked_returns_0(self):
        h, driver = _make_handler()
        reg = _make_register()
        driver.get_entity_data.return_value = {"state": "unlocked", "attributes": {}}

        result = h.scrape(register=reg)

        assert result == 0

    def test_scrape_jammed_returns_raw_state(self):
        h, driver = _make_handler()
        reg = _make_register()
        driver.get_entity_data.return_value = {"state": "jammed", "attributes": {}}

        result = h.scrape(register=reg)

        assert result == "jammed"

    def test_scrape_unavailable_returns_raw_state(self):
        h, driver = _make_handler()
        reg = _make_register()
        driver.get_entity_data.return_value = {"state": "unavailable", "attributes": {}}

        result = h.scrape(register=reg)

        assert result == "unavailable"

    def test_scrape_attribute_returns_attribute_value(self):
        h, driver = _make_handler()
        reg = _make_register(entity_point="friendly_name")
        driver.get_entity_data.return_value = {
            "state": "locked",
            "attributes": {"friendly_name": "Front Door Lock"},
        }

        result = h.scrape(register=reg)

        assert result == "Front Door Lock"