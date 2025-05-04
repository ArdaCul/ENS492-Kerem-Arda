import os
import json
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from device_manager import DeviceManager
from energy_manager import EnergyManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

# Configuration file paths
CONFIG_FILE = 'config.json'
DEVICE_CONFIG_FILE = 'devices.json'

# Default configurations
DEFAULT_CONFIG = {
    "tapo_username": "",
    "tapo_password": "",
    "grid_enabled": True,
    "grid_max_power": 10000,  # Watts
    "home_battery_enabled": True,
    "home_battery_capacity": 10.0,  # kWh
    "home_battery_level": 50,  # %
    "home_battery_max_output": 5000,  # Watts
    "home_battery_max_input": 3500,  # Watts
    "home_battery_mode": "idle",  # idle, charging, in_use
    "car_battery_enabled": False,
    "car_battery_capacity": 75.0,  # kWh
    "car_battery_level": 80,  # %
    "car_battery_max_output": 7500,  # Watts
    "car_battery_max_input": 11000,  # Watts
    "car_battery_mode": "idle",  # idle, charging, in_use
    "car_connected": False,
    "electricity_rate": 0.15,  # $/kWh
    "power_priorities": ["grid", "home_battery", "car_battery"]
}

DEFAULT_DEVICES = {
    "real_devices": [],
    "mock_devices": [
        {
            "id": "mock-fridge",
            "name": "Refrigerator",
            "type": "refrigerator",
            "avg_power": 100,  # Watts
            "is_on": True,
            "is_dimmable": False
        },
        {
            "id": "mock-tv",
            "name": "Living Room TV",
            "type": "tv",
            "avg_power": 150,  # Watts
            "is_on": False,
            "is_dimmable": False
        },
        {
            "id": "mock-light",
            "name": "Kitchen Lights",
            "type": "light",
            "avg_power": 60,  # Watts
            "is_on": False,
            "is_dimmable": True,
            "dimming_level": 100  # %
        }
    ]
}

# Load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG

# Save configuration
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_devices():
    """Load device configuration"""
    if os.path.exists(DEVICE_CONFIG_FILE):
        try:
            with open(DEVICE_CONFIG_FILE, 'r') as f:
                content = f.read().strip()
                # Check if the file is empty or invalid JSON
                if not content:
                    logger.warning(f"Device config file {DEVICE_CONFIG_FILE} is empty, using defaults")
                    return DEFAULT_DEVICES
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing device config file: {str(e)}, using defaults")
                    return DEFAULT_DEVICES
        except Exception as e:
            logger.error(f"Error loading devices: {str(e)}")
            return DEFAULT_DEVICES
    logger.info(f"Device config file {DEVICE_CONFIG_FILE} not found, using defaults")
    return DEFAULT_DEVICES

# Save device configuration
def save_devices(devices):
    with open(DEVICE_CONFIG_FILE, 'w') as f:
        json.dump(devices, f, indent=4)

# Initialize managers
config = load_config()
devices = load_devices()
device_manager = DeviceManager(config.get('tapo_username', ''), config.get('tapo_password', ''), devices)
energy_manager = EnergyManager(config, device_manager)

@app.route('/')
def index():
    """Welcome/login page"""
    config = load_config()
    if config.get('tapo_username') and config.get('tapo_password'):
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    config = load_config()
    devices = load_devices()
    return render_template('dashboard.html', config=config, devices=devices)

@app.route('/godmode')
def godmode():
    """Simulation control panel"""
    config = load_config()
    return render_template('godmode.html', config=config)

@app.route('/settings')
def settings():
    """Device settings page"""
    config = load_config()
    devices = load_devices()
    return render_template('settings.html', config=config, devices=devices)

@app.route('/api/setup', methods=['POST'])
def setup():
    """Initial setup with Tapo credentials"""
    data = request.json
    config = load_config()
    
    config['tapo_username'] = data.get('username', '')
    config['tapo_password'] = data.get('password', '')
    
    save_config(config)
    
    # Update device manager
    device_manager.update_credentials(config['tapo_username'], config['tapo_password'])
    
    return jsonify({"success": True})

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Get or update configuration"""
    if request.method == 'GET':
        return jsonify(load_config())
    
    data = request.json
    config = load_config()
    
    # Update configuration with provided values
    for key, value in data.items():
        if key in config:
            config[key] = value
    
    save_config(config)
    
    # Update energy manager
    energy_manager.update_config(config)
    
    return jsonify({"success": True})

@app.route('/api/devices', methods=['GET'])
def api_devices():
    """Get all devices"""
    return jsonify(load_devices())

@app.route('/api/devices/add', methods=['POST'])
def add_device():
    """Add a new device"""
    data = request.json
    devices = load_devices()
    
    if data.get('type') == 'real':
        # Real Tapo device
        devices['real_devices'].append({
            "id": data.get('id'),
            "name": data.get('name'),
            "type": data.get('device_type'),
            "ip": data.get('ip'),
            "is_on": False
        })
    else:
        # Mock device
        devices['mock_devices'].append({
            "id": f"mock-{data.get('id')}",
            "name": data.get('name'),
            "type": data.get('device_type'),
            "avg_power": float(data.get('avg_power', 100)),
            "is_on": False,
            "is_dimmable": data.get('is_dimmable', False) == 'true',
            "dimming_level": 100 if data.get('is_dimmable', False) == 'true' else None
        })
    
    save_devices(devices)
    
    # Update device manager
    device_manager.update_devices(devices)
    
    return jsonify({"success": True})

@app.route('/api/devices/remove', methods=['POST'])
def remove_device():
    """Remove a device"""
    data = request.json
    device_id = data.get('id')
    devices = load_devices()
    
    # Remove from real devices
    devices['real_devices'] = [d for d in devices['real_devices'] if d['id'] != device_id]
    
    # Remove from mock devices
    devices['mock_devices'] = [d for d in devices['mock_devices'] if d['id'] != device_id]
    
    save_devices(devices)
    
    # Update device manager
    device_manager.update_devices(devices)
    
    return jsonify({"success": True})

@app.route('/api/devices/control', methods=['POST'])
def control_device():
    """Control a device (turn on/off, adjust)"""
    data = request.json
    device_id = data.get('id')
    action = data.get('action')
    value = data.get('value')
    
    result = device_manager.control_device(device_id, action, value)
    
    # Update devices configuration
    devices = load_devices()
    
    # Update real devices
    for device in devices['real_devices']:
        if device['id'] == device_id:
            if action == 'power':
                device['is_on'] = value
            elif action == 'dimming' and 'dimming_level' in device:
                device['dimming_level'] = value
    
    # Update mock devices
    for device in devices['mock_devices']:
        if device['id'] == device_id:
            if action == 'power':
                device['is_on'] = value
            elif action == 'dimming' and 'dimming_level' in device:
                device['dimming_level'] = value
    
    save_devices(devices)
    
    return jsonify(result)

@app.route('/api/battery/control', methods=['POST'])
def control_battery():
    """Control home or car battery"""
    data = request.json
    battery_type = data.get('type')  # 'home' or 'car'
    action = data.get('action')  # 'charge', 'discharge', 'connect', 'disconnect'
    
    config = load_config()
    
    # Only allow actions if batteries are enabled
    if battery_type == 'home' and config.get('home_battery_enabled', True):
        if action == 'charge':
            # Logic for charging home battery from grid
            pass
        elif action == 'discharge':
            # Logic for discharging home battery to home
            pass
    elif battery_type == 'car' and config.get('car_battery_enabled', False):
        if action == 'connect':
            config['car_connected'] = True
            # Set car battery to idle mode when connected
            config['car_battery_mode'] = 'idle'
        elif action == 'disconnect':
            config['car_connected'] = False
        elif action == 'charge':
            # Logic for charging car battery from grid
            pass
        elif action == 'discharge':
            # Logic for discharging car battery to home
            pass
    
    save_config(config)
    
    # Update energy manager
    energy_manager.update_config(config)
    
    return jsonify({"success": True})

@app.route('/api/battery/mode', methods=['POST'])
def battery_mode():
    """Set battery mode (idle, charging, in_use)"""
    data = request.json
    battery_type = data.get('type')  # 'home' or 'car'
    mode = data.get('mode')  # 'idle', 'charging', 'in_use'
    
    result = energy_manager.set_battery_mode(battery_type, mode)
    
    if result:
        config = load_config()
        if battery_type == 'home':
            config['home_battery_mode'] = mode
        elif battery_type == 'car':
            config['car_battery_mode'] = mode
        save_config(config)
    
    return jsonify({"success": result})

@app.route('/api/power/priority', methods=['POST'])
def power_priority():
    """Update power source priorities"""
    data = request.json
    priorities = data.get('priorities', [])
    
    result = energy_manager.update_power_priority(priorities)
    
    if result:
        # Store priorities in config
        config = load_config()
        config['power_priorities'] = priorities
        save_config(config)
        
        # Update energy manager
        energy_manager.update_config(config)
    
    return jsonify({
        "success": result
    })

@app.route('/api/power/distribution', methods=['POST'])
def power_distribution():
    """Legacy endpoint for backward compatibility"""
    return jsonify({
        "success": True,
        "actual": {
            "grid": 70,
            "home_battery": 20,
            "car_battery": 10
        }
    })

@app.route('/api/energy/status', methods=['GET'])
def energy_status():
    """Get energy status (usage, generation, storage)"""
    try:
        status = energy_manager.get_status()
        logger.info(f"Energy status: Total power={status['total_power_usage']}W, "
                   f"Grid={status['grid_power']}W, "
                   f"Home battery={status['home_battery_power']}W, "
                   f"Car battery={status['car_battery_power']}W")
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting energy status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/energy/history', methods=['GET'])
def energy_history():
    """Get energy usage history"""
    period = request.args.get('period', 'day')  # 'day', 'week', 'month'
    return jsonify(energy_manager.get_history(period))

if __name__ == '__main__':
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
    
    if not os.path.exists(DEVICE_CONFIG_FILE):
        save_devices(DEFAULT_DEVICES)
    
    app.run(host='0.0.0.0', port=5000, debug=True)