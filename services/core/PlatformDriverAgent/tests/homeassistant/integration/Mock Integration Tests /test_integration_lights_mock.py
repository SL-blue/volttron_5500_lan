from unittest.mock import MagicMock, patch

from platform_driver.interfaces.home_assistant import Interface


def make_driver_config():
    return {
        "ip_address": "127.0.0.1",
        "access_token": "test-token",
        "port": 8123,
    }


def make_light_registry():
    return [{
        "Entity ID": "light.living_room",
        "Entity Point": "state",
        "Volttron Point Name": "living_room_light",
        "Units": "On / Off",
        "Writable": "true",
        "Starting Value": 0,
        "Type": "int",
        "Notes": "Living room light state",
    }]


def make_mock_response(state):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"state": state, "attributes": {}}
    return response


def make_mock_post_response():
    response = MagicMock()
    response.status_code = 200
    response.text = ""
    return response


@patch("platform_driver.interfaces.home_assistant.requests.get")
def test_get_point_light_on_via_configured_interface(mock_get):
    # Create the real Home Assistant interface object we want to test.
    interface = Interface()

    # Build a fake HTTP response object.
    # We are pretending that Home Assistant replied successfully.
    # Make the patched requests.get(...) return our fake response.
    mock_get.return_value = make_mock_response("on")

    # Run the real interface setup code.
    # This loads the config, creates registers, and creates the handlers.
    interface.configure(make_driver_config(), make_light_registry())

    # Ask the interface for the point value using the VOLTTRON point name.
    # The interface will:
    # - find the register
    # - choose the light handler
    # - call the Home Assistant state endpoint
    # - convert "on" into 1
    result = interface.get_point("living_room_light")

    print("\n=== TEST: light on -> 1 ===")
    print("Action: calling interface.get_point('living_room_light')")
    print("Expected: 1")
    print(f"Got: {result}")

    # Check that the returned value matches the expected normalized value.
    assert result == 1

    # Check that the interface built the correct HTTP request.
    mock_get.assert_called_once_with(
        "http://127.0.0.1:8123/api/states/light.living_room",
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
    )


@patch("platform_driver.interfaces.home_assistant.requests.post")
@patch("platform_driver.interfaces.home_assistant.requests.get")
def test_set_point_light_off_to_on_via_configured_interface(mock_get, mock_post):
    interface = Interface()

    # First read says the light is off.
    # Second read says the light is on after the write.
    mock_get.side_effect = [
        make_mock_response("off"),
        make_mock_response("on"),
    ]
    mock_post.return_value = make_mock_post_response()

    interface.configure(make_driver_config(), make_light_registry())

    before = interface.get_point("living_room_light")
    written = interface.set_point("living_room_light", 1)
    after = interface.get_point("living_room_light")

    print("\n=== TEST: light off -> on ===")
    print("Action: calling interface.set_point('living_room_light', 1)")
    print("Expected before: 0")
    print(f"Got before: {before}")
    print("Expected written value: 1")
    print(f"Got written value: {written}")
    print("Expected after: 1")
    print(f"Got after: {after}")

    assert before == 0
    assert written == 1
    assert after == 1

    mock_post.assert_called_once_with(
        "http://127.0.0.1:8123/api/services/light/turn_on",
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
        json={"entity_id": "light.living_room"},
    )
