import pytest
import requests
import subprocess

def check_volttron_is_scraping():
    result = subprocess.run([
        'ssh', '-i', '/Users/paulaminozzo/.ssh/volttron_vm', '-p', '2222', 'paula-minozzo@localhost',
        'grep "scraping device: home/homeassistant" ~/volttron/volttron.log | tail -1'
    ], capture_output=True, text=True)
    return "scraping device" in result.stdout

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

# Makes a GET request to lock.test_lock and checks the response status is 200
def test_get_lock_state():
    response = requests.get(f"{HA_URL}/api/states/lock.test_lock", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    print("\n=== TEST: GET lock state ===")
    print(f"\nVOLTTRON scraping: {check_volttron_is_scraping()}")
    assert check_volttron_is_scraping(), "VOLTTRON is not scraping Home Assistant!"
    assert "state" in data
    assert data["state"] in ["locked", "unlocked"]
    print(f"Response: {response.text}")
    response_message = get_status_message(response.status_code)
    print(f"Status: {response.status_code} - {response_message}")
    print(f"Lock state is: {data['state']}")

# Makes a POST request to lock the lock entity
def test_lock_lock():
    response = requests.post(f"{HA_URL}/api/services/lock/lock", headers=HEADERS, json={"entity_id": "lock.test_lock"})
    print("\n=== TEST: LOCK the lock ===")
    print(f"Response: {response.text}")
    response_message = get_status_message(response.status_code)
    print(f"Status: {response.status_code} - {response_message}")
    print(f"\nVOLTTRON scraping: {check_volttron_is_scraping()}")
    assert check_volttron_is_scraping(), "VOLTTRON is not scraping Home Assistant!"
    assert response.status_code == 200

# Makes a POST request to unlock the lock entity
def test_lock_unlock():
    response = requests.post(f"{HA_URL}/api/services/lock/unlock", headers=HEADERS, json={"entity_id": "lock.test_lock"})
    print("\n=== TEST: UNLOCK the lock ===")
    print(f"Response: {response.text}")
    response_message = get_status_message(response.status_code)
    print(f"Status: {response.status_code} - {response_message}")
    print(f"\nVOLTTRON scraping: {check_volttron_is_scraping()}")
    assert check_volttron_is_scraping(), "VOLTTRON is not scraping Home Assistant!"
    assert response.status_code == 200