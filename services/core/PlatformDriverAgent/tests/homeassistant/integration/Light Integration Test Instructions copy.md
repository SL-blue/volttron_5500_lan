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
- Ubuntu VM with VOLTTRON running (for full stack verification)
- SSH key configured from your Mac to the VM (passwordless)
- Note your Ubuntu VM username (run `whoami` in the VM to find it)

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

## Step 6 — Install Python Dependencies

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

Each test also verifies VOLTTRON is actively scraping Home Assistant
by SSHing into your Ubuntu VM and checking the VOLTTRON log for:
`scraping device: home/homeassistant`

This proves the full stack is working:
Mac (pytest) → Home Assistant API → VOLTTRON driver → VOLTTRON message bus

Note: The `check_volttron_is_scraping()` function in the test file uses
your SSH key to connect to the VM automatically without a password.

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
