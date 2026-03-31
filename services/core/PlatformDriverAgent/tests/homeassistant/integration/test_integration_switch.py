import pytest
import requests

STATUS_CODES = {
    200: "Success - request worked perfectly",
    400: "Bad Request - your JSON or parameters are malformed",
    401: "Unauthorized - your token is wrong or missing",
    403: "Forbidden - your token does not have permission",
    404: "Not Found - entity ID does not exist, check for typos",
    500: "Internal Server Error - Home Assistant crashed",
    503: "Service Unavailable - Home Assistant is still starting up"
}

def get_status_message(code):
    return STATUS_CODES.get(code, "Unknown status code")

HA_URL = "http://localhost:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI2NzVhNTZkYWIwODQ0MzM2YmY4MWZlNmJhMjAxNjhiNSIsImlhdCI6MTc3NDgyNTYyOCwiZXhwIjoyMDkwMTg1NjI4fQ._bPz-KYWEGLVaONTMtO9z-7U_xbClqxNF2ZaiEuyj0I"
HEADERS = {"Authorization": "Bearer " + TOKEN}

def test_get_switch_state ():
    response = requests.get(f"{HA_URL}/api/states/switch.test_switch", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    print("\n=== TEST: GET switch state ===")
    assert "state" in data
    assert data["state"] in ["on", "off"]
    response_message = get_status_message(response.status_code)
    print(f"Status: {response.status_code} - {response_message}")
    print(f"Switch state is: {data['state']}")

def test_set_switch_on():
    response = requests.post(f"{HA_URL}/api/services/switch/turn_on", headers=HEADERS, json={"entity_id": "switch.test_switch"})
    print("\n=== TEST: Set switch ON ===")
    print(f"Response: {response.text}")
    print(f"Status: {response.status_code} - {get_status_message(response.status_code)}")
    assert response.status_code == 200

def test_set_switch_off():
    response = requests.post(f"{HA_URL}/api/services/switch/turn_off", headers=HEADERS, json={"entity_id": "switch.test_switch"})
    print("\n=== TEST: Set switch OFF ===")
    print(f"Response: {response.text}")
    print(f"Status: {response.status_code} - {get_status_message(response.status_code)}")
    assert response.status_code == 200