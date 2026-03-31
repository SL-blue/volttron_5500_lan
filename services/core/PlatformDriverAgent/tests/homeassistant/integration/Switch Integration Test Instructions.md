# Switch Integration Tests

These tests verify that the VOLTTRON Home Assistant driver can interact with
a real `switch` entity in Home Assistant. Unlike unit tests which use mocks,
these tests make real HTTP requests and actually toggle the switch state.

---

## What is a Template Switch?

Since real switch entities require physical hardware (like a smart plug),
we create a **template switch** — a virtual `switch.` entity that behaves
exactly like a real switch from the API's perspective. It lives entirely
in software inside Home Assistant.

Our template switch (`switch.test_switch`) mirrors the state of
`input_boolean.test_a` — when you turn it on via the API, Home Assistant
records the state change and responds exactly like real hardware would.

---

## Prerequisites

Before running these tests you need:

- Docker Desktop installed and running
- Home Assistant running in Docker at `http://localhost:8123`
- A Long-Lived Access Token from Home Assistant
- The `input_boolean.test_a` helper created in Home Assistant
- The `switch.test_switch` template switch configured in `configuration.yaml`
- `pytest` and `requests` Python packages installed

If you haven't set up Home Assistant yet, follow the instructions in `README.md` first.

---

## Step 1 — Create the input_boolean Helper

This is the virtual toggle that powers our template switch.

1. Go to `http://localhost:8123`
2. Click **Settings → Devices & Services → Helpers**
3. Click **+ Create Helper → Toggle**
4. Name it `test_a`
5. Click **Create**

Your entity ID will be `input_boolean.test_a`.

---

## Step 2 — Create the Template Switch

This creates a real `switch.test_switch` entity by editing the Home Assistant
configuration file directly.

Run this command in your terminal:

```bash
cat > ~/homeassistant/configuration.yaml << 'EOF'
# Loads default set of integrations. Do not remove.
default_config:

# Load frontend themes from the themes folder
frontend:
  themes: !include_dir_merge_named themes

automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml

switch:
  - platform: template
    switches:
      test_switch:
        value_template: "{{ states('input_boolean.test_a') == 'on' }}"
        turn_on:
          service: input_boolean.turn_on
          target:
            entity_id: input_boolean.test_a
        turn_off:
          service: input_boolean.turn_off
          target:
            entity_id: input_boolean.test_a
EOF
```

Then restart Home Assistant to pick up the new configuration:

```bash
docker restart homeassistant
```

Wait 2-3 minutes for it to fully restart.

---

## Step 3 — Verify the Switch Entity Exists

Run this curl command to confirm `switch.test_switch` was created successfully
(replace `YOUR_TOKEN` with your actual token):

```bash
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8123/api/states/switch.test_switch | python3 -m json.tool
```

You should see:
```json
{
    "entity_id": "switch.test_switch",
    "state": "off",
    ...
}
```

---

## Step 4 — Configure the Test File

Open `test_integration_switch.py` and update these constants at the top:

```python
HA_URL = "http://localhost:8123"
TOKEN = "paste_your_token_here"
```

---

## Step 5 — Install Python Dependencies

```bash
pip install pytest requests --break-system-packages
```

---

## Step 6 — Run the Tests

Navigate to the integration test folder:

```bash
cd services/core/PlatformDriverAgent/tests/homeassistant/integration
```

### Run ALL switch tests:
```bash
pytest test_integration_switch.py -v -s
```

### Run ONLY the get state test:
```bash
pytest test_integration_switch.py::test_get_switch_state -v -s
```

### Run ONLY the turn on test:
```bash
pytest test_integration_switch.py::test_set_switch_on -v -s
```

### Run ONLY the turn off test:
```bash
pytest test_integration_switch.py::test_set_switch_off -v -s
```

---

## What the Tests Do

**`test_get_switch_state`**
Calls `GET /api/states/switch.test_switch` and verifies:
- Response status is 200
- Response contains a `state` field
- State is either `on` or `off`

**`test_set_switch_on`**
Calls `POST /api/services/switch/turn_on` and verifies:
- Response status is 200
- The switch was actually turned on

**`test_set_switch_off`**
Calls `POST /api/services/switch/turn_off` and verifies:
- Response status is 200
- The switch was actually turned off

---

## Watching Tests Run in Real Time

Open `http://localhost:8123` in your browser while running tests.
Go to **Settings → Devices & Services → Helpers** and watch
`test_a` toggle on and off as each test runs — this confirms
real state changes are happening!

---

## Understanding Status Codes

The tests print a human readable status message for every response:

| Code | Meaning |
|------|---------|
| 200  | Success - request worked perfectly |
| 400  | Bad Request - JSON or parameters are malformed |
| 401  | Unauthorized - token is wrong or missing |
| 403  | Forbidden - token does not have permission |
| 404  | Not Found - entity ID does not exist, check for typos |
| 500  | Internal Server Error - Home Assistant crashed |
| 503  | Service Unavailable - Home Assistant is still starting up |

---

## Manually Control the Switch from Command Line

### Turn switch ON:
```bash
curl -s -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.test_switch"}' \
  http://localhost:8123/api/services/switch/turn_on
```

### Turn switch OFF:
```bash
curl -s -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.test_switch"}' \
  http://localhost:8123/api/services/switch/turn_off
```

### Check current state:
```bash
curl -s \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8123/api/states/switch.test_switch | python3 -m json.tool | grep state
```

---

## Difference Between Switch and Input Boolean Tests

| Feature | input_boolean | switch |
|---------|--------------|--------|
| Entity ID prefix | `input_boolean.` | `switch.` |
| Service domain | `input_boolean` | `switch` |
| API URL | `/api/services/input_boolean/turn_on` | `/api/services/switch/turn_on` |
| Requires hardware | No | No (template switch) |
| Real world use | Testing only | Smart plugs, real switches |

---

## Troubleshooting

**`switch.test_switch` not found:**
Home Assistant may still be restarting. Wait 2-3 minutes and try again.
Check logs with:
```bash
docker logs homeassistant --tail 20
```

**Tests not collected (0 items):**
Make sure you are in the integration folder and both `conftest.py`
and `pytest.ini` exist:
```bash
ls conftest.py pytest.ini
```

**Switch state not changing:**
Verify `input_boolean.test_a` exists in Home Assistant.
The template switch depends on it — if `test_a` is missing,
`switch.test_switch` won't work.