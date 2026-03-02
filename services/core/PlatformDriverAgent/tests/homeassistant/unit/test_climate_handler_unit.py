import pytest

from platform_driver.interfaces.homeassistant_handlers.climate import ClimateHandler


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


@pytest.mark.parametrize(
    "mode_int,mode_str",
    [(0, "off"), (2, "heat"), (3, "cool"), (4, "auto")],
)
def test_climate_set_point_state_calls_set_hvac_mode(mode_int, mode_str):
    driver = FakeDriver()
    handler = ClimateHandler(driver)

    reg = FakeRegister("climate.living_room", "state", "hvac_mode")
    handler.set_point(register=reg, value=mode_int)

    assert len(driver.calls) == 1
    call = driver.calls[0]
    assert call["domain"] == "climate"
    assert call["service"] == "set_hvac_mode"
    assert call["payload"] == {"entity_id": "climate.living_room", "hvac_mode": mode_str}


def test_climate_set_point_state_rejects_invalid_mode():
    driver = FakeDriver()
    handler = ClimateHandler(driver)

    reg = FakeRegister("climate.living_room", "state", "hvac_mode")
    with pytest.raises(ValueError):
        handler.set_point(register=reg, value=1)  # invalid per mapping


def test_climate_set_point_temperature_sends_value_direct_when_units_not_C():
    driver = FakeDriver(units="F")  # anything other than "C" means "send as-is"
    handler = ClimateHandler(driver)

    reg = FakeRegister("climate.living_room", "temperature", "setpoint")
    handler.set_point(register=reg, value=72)

    assert len(driver.calls) == 1
    call = driver.calls[0]
    assert call["domain"] == "climate"
    assert call["service"] == "set_temperature"
    assert call["payload"] == {"entity_id": "climate.living_room", "temperature": 72}


def test_climate_set_point_temperature_converts_f_to_c_when_units_C():
    driver = FakeDriver(units="C")  # Converts Fahrenheit input to Celsius
    handler = ClimateHandler(driver)

    reg = FakeRegister("climate.living_room", "temperature", "setpoint")
    handler.set_point(register=reg, value=68)  # 20.0C

    assert len(driver.calls) == 1
    call = driver.calls[0]
    assert call["domain"] == "climate"
    assert call["service"] == "set_temperature"
    assert call["payload"]["entity_id"] == "climate.living_room"
    assert call["payload"]["temperature"] == 20.0


def test_climate_set_point_temperature_rejects_non_numeric():
    driver = FakeDriver()
    handler = ClimateHandler(driver)

    reg = FakeRegister("climate.living_room", "temperature", "setpoint")
    with pytest.raises(ValueError):
        handler.set_point(register=reg, value="hot")


@pytest.mark.parametrize(
    "ha_state,expected",
    [("off", 0), ("heat", 2), ("cool", 3), ("auto", 4)],
)
def test_climate_scrape_state_maps_to_ints(ha_state, expected):
    driver = FakeDriver()
    driver._entity_data["climate.living_room"] = {"state": ha_state, "attributes": {"temperature": 70}}
    handler = ClimateHandler(driver)

    reg = FakeRegister("climate.living_room", "state", "hvac_mode")
    assert handler.scrape(register=reg) == expected


def test_climate_scrape_state_rejects_unknown_state():
    driver = FakeDriver()
    driver._entity_data["climate.living_room"] = {"state": "dry", "attributes": {}}
    handler = ClimateHandler(driver)

    reg = FakeRegister("climate.living_room", "state", "hvac_mode")
    with pytest.raises(ValueError):
        handler.scrape(register=reg)


def test_climate_scrape_attribute_returns_attribute_value_or_0():
    driver = FakeDriver()
    driver._entity_data["climate.living_room"] = {
        "state": "heat",
        "attributes": {"temperature": 70, "current_temperature": 68},
    }
    handler = ClimateHandler(driver)

    reg_temp = FakeRegister("climate.living_room", "temperature", "setpoint")
    assert handler.scrape(register=reg_temp) == 70

    reg_missing = FakeRegister("climate.living_room", "humidity", "humidity")
    assert handler.scrape(register=reg_missing) == 0