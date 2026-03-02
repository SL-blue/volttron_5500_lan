import pytest
from platform_driver.interfaces.homeassistant_handlers.light import LightHandler


class FakeDriver:
    def __init__(self, units=None):
        self.units = units
        self.calls = []
        self._entity_data = {}

    def _call_service(self, domain, service, payload, op_desc=""):
        self.calls.append(
            {"domain": domain, "service": service, "payload": payload, "op_desc": op_desc}
        )

    def get_entity_data(self, entity_id: str):
        return self._entity_data[entity_id]


class FakeRegister:
    def __init__(self, entity_id: str, entity_point: str, point_name: str = "pt"):
        self.entity_id = entity_id
        self.entity_point = entity_point
        self.point_name = point_name


def test_light_set_point_state_on_calls_turn_on():
    driver = FakeDriver()
    handler = LightHandler(driver)

    reg = FakeRegister("light.kitchen", "state", "kitchen_state")
    handler.set_point(register=reg, value=1)

    assert len(driver.calls) == 1
    call = driver.calls[0]
    assert call["domain"] == "light"
    assert call["service"] == "turn_on"
    assert call["payload"] == {"entity_id": "light.kitchen"}


def test_light_set_point_state_off_calls_turn_off():
    driver = FakeDriver()
    handler = LightHandler(driver)

    reg = FakeRegister("light.kitchen", "state", "kitchen_state")
    handler.set_point(register=reg, value=0)

    assert len(driver.calls) == 1
    call = driver.calls[0]
    assert call["domain"] == "light"
    assert call["service"] == "turn_off"
    assert call["payload"] == {"entity_id": "light.kitchen"}


def test_light_set_point_state_rejects_invalid_value():
    driver = FakeDriver()
    handler = LightHandler(driver)

    reg = FakeRegister("light.kitchen", "state", "kitchen_state")
    with pytest.raises(ValueError):
        handler.set_point(register=reg, value=2)  # invalid


def test_light_set_point_brightness_calls_turn_on_with_brightness():
    driver = FakeDriver()
    handler = LightHandler(driver)

    reg = FakeRegister("light.kitchen", "brightness", "kitchen_brightness")
    handler.set_point(register=reg, value=200)

    assert len(driver.calls) == 1
    call = driver.calls[0]
    assert call["domain"] == "light"
    assert call["service"] == "turn_on"
    assert call["payload"] == {"entity_id": "light.kitchen", "brightness": 200}


def test_light_set_point_brightness_rejects_out_of_range():
    driver = FakeDriver()
    handler = LightHandler(driver)

    reg = FakeRegister("light.kitchen", "brightness", "kitchen_brightness")
    with pytest.raises(ValueError):
        handler.set_point(register=reg, value=256)
    with pytest.raises(ValueError):
        handler.set_point(register=reg, value=-1)


def test_light_scrape_state_on_maps_to_1():
    driver = FakeDriver()
    driver._entity_data["light.kitchen"] = {"state": "on", "attributes": {"brightness": 123}}
    handler = LightHandler(driver)

    reg = FakeRegister("light.kitchen", "state", "kitchen_state")
    assert handler.scrape(register=reg) == 1


def test_light_scrape_state_off_maps_to_0():
    driver = FakeDriver()
    driver._entity_data["light.kitchen"] = {"state": "off", "attributes": {"brightness": 123}}
    handler = LightHandler(driver)

    reg = FakeRegister("light.kitchen", "state", "kitchen_state")
    assert handler.scrape(register=reg) == 0


def test_light_scrape_attribute_returns_attribute_value_or_0():
    driver = FakeDriver()
    driver._entity_data["light.kitchen"] = {"state": "on", "attributes": {"brightness": 123}}
    handler = LightHandler(driver)

    reg_brightness = FakeRegister("light.kitchen", "brightness", "kitchen_brightness")
    assert handler.scrape(register=reg_brightness) == 123

    reg_missing = FakeRegister("light.kitchen", "color_temp", "kitchen_color_temp")
    assert handler.scrape(register=reg_missing) == 0