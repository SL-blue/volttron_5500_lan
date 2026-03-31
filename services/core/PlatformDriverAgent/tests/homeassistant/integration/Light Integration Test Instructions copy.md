# Home Assistant Integration Tests

These are integration tests for the VOLTTRON Home Assistant driver.
Unlike unit tests (which use mocks), these tests talk to a **real Home Assistant instance**
and verify that the driver can actually turn entities on and off.

---
(Instructions for Mac and Linux machines)
## What You Need Before Running Tests

- Python 3.12+
- Docker Desktop installed and running
- The `requests` and `pytest` Python packages

---

## Step 1 — Install Docker Desktop

Download and install Docker Desktop from https://www.docker.com/products/docker-desktop/

Or install via Homebrew:
```bash
brew install --cask docker
```

Then open Docker Desktop from your Applications folder and wait for the whale icon in the menu bar to stop animating.

Verify Docker is running:
```bash
docker ps
```

You should see an empty list with no errors.

---

## Step 2 — Start Home Assistant

Run this command to download and start Home Assistant in a Docker container:
```bash
docker run -d \
  --name homeassistant \
  -p 8123:8123 \
  -v ~/homeassistant:/config \
  ghcr.io/home-assistant/home-assistant:stable
```

Wait about 2-3 minutes for Home Assistant to fully start, then open your browser at:
```
http://localhost:8123
```

Complete the setup wizard:
1. Create an account (remember your username and password)
2. Name your home anything (e.g. "Test Home")
3. Set location to anywhere
4. Skip any device discovery

---

## Step 3 — Create a Long-Lived Access Token

This token is how your tests authenticate with Home Assistant.

1. Click your **profile icon** at the bottom left of the sidebar
2. Scroll down to **Long-Lived Access Tokens**
3. Click **Create Token**
4. Name it `volttron`
5. **Copy the token immediately** — you only see it once!

---

## Step 4 — Create Test Entities (Virtual Devices)

These are virtual on/off switches inside Home Assistant — no real hardware needed.

1. Go to **Settings → Devices & Services → Helpers**
2. Click **+ Create Helper → Toggle**
3. Name it `test_light` → Click **Create**
4. Repeat and create another called `test_a`

Your entity IDs will be:
- `input_boolean.test_light`
- `input_boolean.test_a`

Verify them by going to:
```
http://localhost:8123/developer-tools/state
```

---

## Step 5 — Configure the Test File

Open `test_integration_lights.py` and update these two constants at the top:

```python
HA_URL = "http://localhost:8123"
TOKEN = "paste_your_token_here"
```

---

## Step 6 — Install Python Dependencies

```bash
pip install pytest requests --break-system-packages
```

---

## Step 7 — Run the Tests

Navigate to the integration test folder:
```bash
cd services/core/PlatformDriverAgent/tests/homeassistant/integration
```

### Run ALL tests:
```bash
pytest test_integration_lights.py -v -s
```

### Run ONLY the get state test:
```bash
pytest test_integration_lights.py::test_get_light_state -v -s
```

### Run ONLY the turn on test:
```bash
pytest test_integration_lights.py::test_set_light_on -v -s
```

### Run ONLY the turn off test:
```bash
pytest test_integration_lights.py::test_set_light_off -v -s
```

The `-v` flag means **verbose** — shows detailed output for each test.
The `-s` flag means **show print statements** — shows your log output.

---

## Watching Tests Run in Real Time

Open your browser at `http://localhost:8123` while running the tests.
Go to **Settings → Devices & Services → Helpers** and watch `test_light` toggle on and off as each test runs!

---

## Manually Toggle Entities from the Command Line

You can also control entities directly using `curl` (replace `YOUR_TOKEN` with your token):

### Turn light ON:
```bash
curl -s -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "input_boolean.test_light"}' \
  http://localhost:8123/api/services/input_boolean/turn_on
```

### Turn light OFF:
```bash
curl -s -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "input_boolean.test_light"}' \
  http://localhost:8123/api/services/input_boolean/turn_off
```

### Check current state:
```bash
curl -s \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8123/api/states/input_boolean.test_light | python3 -m json.tool | grep state
```

---

## Stopping Home Assistant

When you're done testing, stop and remove the container:
```bash
docker stop homeassistant
docker rm homeassistant
```

To start it again later:
```bash
docker start homeassistant
```

---

## Troubleshooting

**`http://localhost:8123` not loading:**
Home Assistant is still starting up. Wait 2-3 minutes and try again. Check logs with:
```bash
docker logs homeassistant --tail 20
```

**`collected 0 items` when running pytest:**
You're in the wrong folder. Make sure you `cd` into the `integration` folder first.

**`ImportError` about conftest.py:**
Make sure there is an empty `conftest.py` and a `pytest.ini` file in the integration folder:
```bash
touch conftest.py
echo "[pytest]
rootdir = ." > pytest.ini
```

**Token not working:**
Generate a new token from your Home Assistant profile page and update `TOKEN` in the test file.