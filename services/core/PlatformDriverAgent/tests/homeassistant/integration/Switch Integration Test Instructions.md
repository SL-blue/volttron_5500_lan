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
- Ubuntu VM with VOLTTRON running (for full stack verification)
- SSH key configured from your Mac to the VM (passwordless)
- Note your Ubuntu VM username (run `whoami` in the VM to find it)

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

Before running the tests you MUST update the `check_volttron_is_scraping()`
function in the test file to match your own username.

Find this function at the top of the test file:

```python
def check_volttron_is_scraping():
    result = subprocess.run([
        'ssh', '-i', '/Users/paulaminozzo/.ssh/volttron_vm', '-p', '2222', 'paula-minozzo@localhost',
        'grep "scraping device: home/homeassistant" ~/volttron/volttron.log | tail -1'
    ], capture_output=True, text=True)
    return "scraping device" in result.stdout
```

Replace two things:

1. Replace `paulaminozzo` in the SSH key path with your Mac username
   - Find your Mac username by running `whoami` on your Mac
   - Example: `/Users/YOUR_MAC_USERNAME/.ssh/volttron_vm`

2. Replace `paula-minozzo` in the SSH command with your Ubuntu VM username
   - Find your VM username by running `whoami` in your VM terminal
   - Example: `YOUR_VM_USERNAME@localhost`

The corrected function should look like:

```python
def check_volttron_is_scraping():
    result = subprocess.run([
        'ssh', '-i', '/Users/YOUR_MAC_USERNAME/.ssh/volttron_vm', '-p', '2222', 'YOUR_VM_USERNAME@localhost',
        'grep "scraping device: home/homeassistant" ~/volttron/volttron.log | tail -1'
    ], capture_output=True, text=True)
    return "scraping device" in result.stdout
```

Before running the tests, update these values in each test file:

1. `TOKEN` in all test files
   Find: `TOKEN = "eyJhbGci..."`
   Replace: `TOKEN = "your_home_assistant_token_here"`
   How to get it: Home Assistant → Profile → Long-Lived Access Tokens → Create Token

2. SSH key path in `check_volttron_is_scraping()`
   Find: `'/Users/paulaminozzo/.ssh/volttron_vm'`
   Replace: `'/Users/YOUR_MAC_USERNAME/.ssh/volttron_vm'`
   How to find your Mac username: run `whoami` in your Mac terminal

3. VM username in `check_volttron_is_scraping()`
   Find: `'paula-minozzo@localhost'`
   Replace: `'YOUR_VM_USERNAME@localhost'`
   How to find your VM username: run `whoami` in your Ubuntu VM terminal

Quick checklist:
- [ ] Updated `TOKEN` in `test_integration_lights.py`
- [ ] Updated `TOKEN` in `test_integration_switch.py`
- [ ] Updated `TOKEN` in `test_integration_lock.py`
- [ ] Updated SSH key path in all three test files
- [ ] Updated VM username in all three test files
- [ ] Created `input_boolean.test_light` helper in Home Assistant
- [ ] Created `input_boolean.test_a` helper in Home Assistant
- [ ] Created `switch.test_switch` via `configuration.yaml`
- [ ] Created `lock.test_lock` in Home Assistant
- [ ] SSH keys set up and passwordless connection works
- [ ] VOLTTRON running in Ubuntu VM
- [ ] Home Assistant driver configured in VOLTTRON

---

## Step 5 — Install Python Dependencies

```bash
pip install pytest requests --break-system-packages
```

---

## Set Up SSH Keys for VOLTTRON Verification

Replace `YOUR_VM_USERNAME` with your actual Ubuntu username.
Run `whoami` in your VM terminal to find it.

### Step 1 - Find your VM username

In your VM terminal:
```bash
whoami
```

### Step 2 - Find your VM IP and set up port forwarding in VirtualBox

In `VirtualBox Settings → Network → Advanced → Port Forwarding` add:

- Name: `SSH`
- Protocol: `TCP`
- Host Port: `2222`
- Guest Port: `22`

### Step 3 - Generate SSH key on your Mac

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/volttron_vm -N ""
```

### Step 4 - Copy key to VM

Enter your password one last time:
```bash
ssh-copy-id -p 2222 -i ~/.ssh/volttron_vm.pub YOUR_VM_USERNAME@localhost
```

### Step 5 - Configure SSH

```bash
echo "Host localhost
  Port 2222
  User YOUR_VM_USERNAME
  IdentityFile ~/.ssh/volttron_vm" >> ~/.ssh/config
```

### Step 6 - Verify it works without a password

```bash
ssh -p 2222 YOUR_VM_USERNAME@localhost "echo connected"
```

---

## VOLTTRON Setup

Replace `YOUR_VM_USERNAME` with your Ubuntu username.
Replace `YOUR_TOKEN` with your Home Assistant long-lived access token.

### SSH into your VM from your Mac

```bash
ssh -p 2222 YOUR_VM_USERNAME@localhost
```

### Start VOLTTRON

```bash
cd ~/volttron && source env/bin/activate
volttron -vv -l volttron.log &
volttron-ctl start 4
```

### Check VOLTTRON is running

```bash
volttron-ctl status
```

You should see `platform_driveragent` running `[GOOD]`.

### Configure the Home Assistant driver

```bash
cat > /tmp/homeassistant.csv << 'EOF'
Entity ID,Entity Point,Volttron Point Name,Units,Type,Writable,Notes
input_boolean.test_light,state,test_light,,int,TRUE,Virtual test light
switch.test_switch,state,test_switch,,int,TRUE,Virtual test switch
EOF

volttron-ctl config store platform.driver homeassistant.csv /tmp/homeassistant.csv --csv

cat > /tmp/homeassistant_driver.json << 'EOF'
{
    "driver_config": {
        "ip_address": "10.0.2.2",
        "access_token": "YOUR_TOKEN",
        "port": 8123
    },
    "driver_type": "home_assistant",
    "registry_config": "config://homeassistant.csv",
    "interval": 60
}
EOF

volttron-ctl config store platform.driver devices/home/homeassistant /tmp/homeassistant_driver.json
```

### Verify VOLTTRON is scraping

```bash
grep "scraping device: home/homeassistant" ~/volttron/volttron.log | tail -5
```

You should see lines like:
```text
platform_driver.driver DEBUG: scraping device: home/homeassistant
platform_driver.driver DEBUG: publishing: devices/home/homeassistant/all
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

Each test also verifies VOLTTRON is actively scraping Home Assistant
by SSHing into your Ubuntu VM and checking the VOLTTRON log for:
`scraping device: home/homeassistant`

This proves the full stack is working:
Mac (pytest) → Home Assistant API → VOLTTRON driver → VOLTTRON message bus

Note: The `check_volttron_is_scraping()` function in the test file uses
your SSH key to connect to the VM automatically without a password.

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

**`VOLTTRON scraping: False` in test output:**
- Make sure your Ubuntu VM is running in VirtualBox
- SSH into your VM and check VOLTTRON status:
```bash
volttron-ctl status
```
- Make sure the Home Assistant driver is configured:
```bash
volttron-ctl config list platform.driver
```
Should show `devices/home/homeassistant`.
- Check VOLTTRON logs:
```bash
grep "home/homeassistant" ~/volttron/volttron.log
```

**SSH asking for password during tests:**
- SSH key is not set up correctly
- Re-run the SSH key setup steps above
- Verify with:
```bash
ssh -p 2222 YOUR_VM_USERNAME@localhost "echo connected"
```

**VM not reachable:**
- Make sure VirtualBox port forwarding is configured on port `2222`
- Make sure your VM is running and fully booted
