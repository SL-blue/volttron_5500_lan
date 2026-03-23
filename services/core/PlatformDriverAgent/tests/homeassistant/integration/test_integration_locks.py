from unittest.mock import MagicMock, patch

from platform_driver.interfaces.home_assistant import Interface


def make_driver_config():
    return {
        "ip_address": "127.0.0.1",
        "access_token": "test-token",
        "port": 8123,
    }


def make_lock_registry():
    return [{
        "Entity ID": "lock.front_door",
        "Entity Point": "state",
        "Volttron Point Name": "front_door_lock",
        "Units": "Locked / Unlocked",
        "Writable": "true",
        "Starting Value": 0,
        "Type": "int",
        "Notes": "Front door lock state",
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
def test_get_point_lock_locked_via_configured_interface(mock_get):
    interface = Interface()

    mock_get.return_value = make_mock_response("locked")

    interface.configure(make_driver_config(), make_lock_registry())

    result = interface.get_point("front_door_lock")

    print("\n=== TEST: lock locked -> 1 ===")
    print("Action: calling interface.get_point('front_door_lock')")
    print("Expected: 1")
    print(f"Got: {result}")

    assert result == 1
    mock_get.assert_called_once_with(
        "http://127.0.0.1:8123/api/states/lock.front_door",
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
    )


@patch("platform_driver.interfaces.home_assistant.requests.post")
@patch("platform_driver.interfaces.home_assistant.requests.get")
def test_set_point_lock_unlocked_to_locked_via_configured_interface(mock_get, mock_post):
    interface = Interface()

    mock_get.side_effect = [
        make_mock_response("unlocked"),
        make_mock_response("locked"),
    ]
    mock_post.return_value = make_mock_post_response()

    interface.configure(make_driver_config(), make_lock_registry())

    before = interface.get_point("front_door_lock")
    written = interface.set_point("front_door_lock", 1)
    after = interface.get_point("front_door_lock")

    print("\n=== TEST: lock unlocked -> locked ===")
    print("Action: calling interface.set_point('front_door_lock', 1)")
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
        "http://127.0.0.1:8123/api/services/lock/lock",
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
        json={"entity_id": "lock.front_door"},
    )
