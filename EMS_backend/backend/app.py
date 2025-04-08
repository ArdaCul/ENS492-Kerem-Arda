import asyncio
import logging
import os
import json
import traceback
from functools import wraps

from flask import Flask, jsonify, request, render_template, redirect, url_for
try:
    from tapo import ApiClient
except ImportError:
    print("Error: Tapo library not found. Please install with: pip install pytapo")
    print("If that doesn't work, try: pip install python-tapo")

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('tapo_app.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Flask app configuration
app = Flask(__name__)

# Config file settings
CONFIG_FILE = 'tapo_config.json'

DEFAULT_CONFIG = {
    "tapo_username": os.environ.get("TAPO_USERNAME", "your_tapo_username"),
    "tapo_password": os.environ.get("TAPO_PASSWORD", "your_tapo_password"),
    "device_ip": os.environ.get("DEVICE_IP", "172.20.10.2")
}

# Global variables
device = None
client = None
is_device_available = False
config_loaded = False
TAPO_USERNAME = DEFAULT_CONFIG["tapo_username"]
TAPO_PASSWORD = DEFAULT_CONFIG["tapo_password"]
DEVICE_IP = DEFAULT_CONFIG["device_ip"]

# Setup event loop for async operations
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return loop.run_until_complete(f(*args, **kwargs))
    return wrapped

def load_config():
    global config_loaded, TAPO_USERNAME, TAPO_PASSWORD, DEVICE_IP
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            logger.info("Configuration loaded from file")
            
            # Update global variables
            TAPO_USERNAME = config.get("tapo_username", DEFAULT_CONFIG["tapo_username"])
            TAPO_PASSWORD = config.get("tapo_password", DEFAULT_CONFIG["tapo_password"])
            DEVICE_IP = config.get("device_ip", DEFAULT_CONFIG["device_ip"])
            
            config_loaded = True
            return config
        else:
            logger.info("No configuration file found, using defaults")
            config_loaded = False
            return DEFAULT_CONFIG
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        config_loaded = False
        return DEFAULT_CONFIG
        
def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        logger.info("Configuration saved to file")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return False

# Initialize the app with config
config = load_config()

@async_action
async def initialize_device():
    global device, client, is_device_available
    try:
        logger.info(f"Attempting to connect to Tapo device at IP: {DEVICE_IP}")
        
        client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
        logger.info("API client created successfully")
        
        device = await client.p110(DEVICE_IP)
        logger.info(f"Successfully connected to Tapo P110 at {DEVICE_IP}")
        is_device_available = True
        return True
    except Exception as e:
        logger.error(f"Failed to connect to device: {str(e)}")
        
        if "InvalidCredentials" in str(e):
            logger.error("Authentication failed - please check your Tapo username and password")
        elif "ConnectionRefused" in str(e) or "ConnectionError" in str(e):
            logger.error(f"Connection refused to {DEVICE_IP} - check if device is powered on and on the same network")
        elif "Timeout" in str(e):
            logger.error(f"Connection timeout to {DEVICE_IP} - device is unreachable")
        
        is_device_available = False
        return False

@app.route('/')
def index():
    global config_loaded
    
    if not config_loaded and (TAPO_USERNAME == "your_tapo_username" or TAPO_PASSWORD == "your_tapo_password"):
        logger.info("No valid configuration found, redirecting to settings")
        return redirect(url_for('settings'))
        
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('settings.html', 
                           tapo_username=TAPO_USERNAME,
                           tapo_password="********" if TAPO_PASSWORD != "your_tapo_password" else "",
                           device_ip=DEVICE_IP,
                           is_default_username=TAPO_USERNAME == "your_tapo_username",
                           is_default_password=TAPO_PASSWORD == "your_tapo_password")

@app.route('/api/status', methods=['GET'])
@async_action
async def get_status():
    global device, is_device_available
    
    logger.info("API: /api/status requested")
    
    if not is_device_available:
        logger.info("Device not available - attempting to initialize connection")
        try:
            if not await initialize_device():
                logger.info("Initialization failed - returning offline status")
                return jsonify({
                    "device_name": "Tapo P110 (Offline)",
                    "is_on": False,
                    "model": "P110",
                    "status": "offline"
                })
        except Exception as e:
            logger.error(f"Error during device initialization in status check: {str(e)}")
            return jsonify({
                "device_name": "Tapo P110 (Error)",
                "is_on": False,
                "status": "error",
                "error_message": str(e)
            })
    
    try:
        logger.info("Requesting device info from Tapo device")
        device_info = await device.get_device_info()
        logger.info("Successfully received device info")
        
        try:
            status = {
                "device_name": str(getattr(device_info, "nickname", getattr(device_info, "name", "Tapo P110"))),
                "is_on": bool(getattr(device_info, "device_on", getattr(device_info, "on", False))),
                "model": str(getattr(device_info, "model", "P110")),
                "firmware_version": str(getattr(device_info, "fw_ver", getattr(device_info, "firmware_version", ""))),
                "status": "online"
            }
            logger.info(f"Extracted status: device_name={status['device_name']}, is_on={status['is_on']}")
        except Exception as e:
            logger.warning(f"Error extracting device info attributes: {str(e)}")
            attrs = dir(device_info)
            status = {"status": "online"}
            for attr in attrs:
                if not attr.startswith("_"):
                    try:
                        value = getattr(device_info, attr)
                        if not callable(value):
                            status[attr] = value
                    except Exception:
                        pass
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Failed to get device status: {str(e)}")
        return jsonify({
            "device_name": "Tapo P110 (Error)",
            "is_on": False,
            "status": "error",
            "error_message": str(e)
        })

@app.route('/api/power/<state>', methods=['POST'])
@async_action
async def set_power(state):
    global device, is_device_available
    
    if not is_device_available:
        try:
            if not await initialize_device():
                return jsonify({
                    "status": "offline", 
                    "message": "Device is not available. Request to turn " + state + " was not processed."
                })
        except Exception as e:
            logger.error(f"Error initializing device: {str(e)}")
            return jsonify({
                "status": "error", 
                "message": f"Error: {str(e)}"
            })
    
    if state.lower() not in ["on", "off"]:
        return jsonify({"error": "State must be 'on' or 'off'"}), 400
    
    try:
        if state.lower() == "on":
            await device.on()
            return jsonify({"status": "success", "message": "Device turned on"})
        else:
            await device.off()
            return jsonify({"status": "success", "message": "Device turned off"})
    except Exception as e:
        logger.error(f"Failed to set power state: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to set power state: {str(e)}"})

@app.route('/api/energy', methods=['GET'])
@async_action
async def get_energy():
    global device, is_device_available
    
    if not is_device_available:
        try:
            if not await initialize_device():
                return jsonify({
                    "current_power_watts": 0.0,
                    "today_energy_kwh": 0.0,
                    "month_energy_kwh": 0.0,
                    "today_runtime": 0,
                    "month_runtime": 0,
                    "status": "offline"
                })
        except Exception as e:
            logger.error(f"Error initializing device: {str(e)}")
            return jsonify({
                "status": "error",
                "error_message": str(e),
                "current_power_watts": 0.0,
                "today_energy_kwh": 0.0,
                "month_energy_kwh": 0.0
            })
    
    try:
        current_power_obj = await device.get_current_power()
        
        if hasattr(current_power_obj, "power"):
            current_power = float(current_power_obj.power)
        elif hasattr(current_power_obj, "current_power"):
            current_power = float(current_power_obj.current_power)
        else:
            try:
                current_power = float(current_power_obj)
            except (TypeError, ValueError):
                current_power = 0.0
        
        energy_data = await device.get_energy_usage()
        
        result = {
            "current_power_watts": current_power,
            "today_energy_kwh": float(getattr(energy_data, "today_energy", getattr(energy_data, "energy_today", 0.0))),
            "month_energy_kwh": float(getattr(energy_data, "month_energy", getattr(energy_data, "energy_month", 0.0))),
            "today_runtime": int(getattr(energy_data, "today_runtime", getattr(energy_data, "runtime_today", 0))),
            "month_runtime": int(getattr(energy_data, "month_runtime", getattr(energy_data, "runtime_month", 0))),
            "status": "online"
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to get energy data: {str(e)}")
        return jsonify({
            "status": "error",
            "error_message": f"Failed to get energy data: {str(e)}",
            "current_power_watts": 0.0,
            "today_energy_kwh": 0.0,
            "month_energy_kwh": 0.0
        })

@app.route('/api/update-settings', methods=['POST'])
@async_action
async def update_settings():
    global TAPO_USERNAME, TAPO_PASSWORD, DEVICE_IP, device, client, is_device_available, config_loaded
    
    try:
        data = request.json
        logger.info(f"Received settings update request for device IP: {data.get('device_ip')}")
        
        new_username = data.get('username', TAPO_USERNAME)
        new_password = data.get('password')
        new_device_ip = data.get('device_ip', DEVICE_IP)
        
        if not new_password:
            new_password = TAPO_PASSWORD
            
        test_result = {
            "success": False,
            "message": "Failed to connect with provided credentials"
        }
        
        try:
            logger.info(f"Testing connection with new credentials to {new_device_ip}")
            
            test_client = ApiClient(new_username, new_password)
            test_device = await test_client.p110(new_device_ip)
            
            await test_device.get_device_info()
            
            logger.info("Connection test successful, updating credentials")
            test_result["success"] = True
            test_result["message"] = "Connection successful! Settings updated."
            
            TAPO_USERNAME = new_username
            TAPO_PASSWORD = new_password
            DEVICE_IP = new_device_ip
            
            new_config = {
                "tapo_username": TAPO_USERNAME,
                "tapo_password": TAPO_PASSWORD,
                "device_ip": DEVICE_IP
            }
            save_config(new_config)
            config_loaded = True
            
            device = None
            client = None
            is_device_available = False
            await initialize_device()
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            error_message = str(e)
            
            if "InvalidCredentials" in error_message:
                test_result["message"] = "Invalid username or password. Please check your Tapo account credentials."
            elif "Connection" in error_message or "Timeout" in error_message:
                test_result["message"] = f"Could not connect to device at {new_device_ip}. Please check the IP address and ensure the device is online."
            else:
                test_result["message"] = f"Connection failed: {error_message}"
                
        return jsonify(test_result)
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error updating settings: {str(e)}"
        })

@app.route('/api/diagnostics', methods=['GET'])
def get_diagnostics():
    import socket
    import platform
    import subprocess
    
    logger.info("Running network diagnostics")
    
    diagnostics = {
        "network": {
            "hostname": socket.gethostname(),
            "local_ip": None,
            "ping_result": None,
            "device_ip": DEVICE_IP
        },
        "device_status": {
            "is_available": is_device_available,
            "tapo_username_set": TAPO_USERNAME != "your_tapo_username",
            "tapo_password_set": TAPO_PASSWORD != "your_tapo_password"
        }
    }
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        diagnostics["network"]["local_ip"] = s.getsockname()[0]
        s.close()
    except Exception as e:
        diagnostics["network"]["local_ip"] = f"Error: {str(e)}"
    
    try:
        if platform.system().lower() == "windows":
            ping_param = "-n"
        else:
            ping_param = "-c"
            
        process = subprocess.Popen(
            ["ping", ping_param, "1", DEVICE_IP],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            diagnostics["network"]["ping_result"] = "Success"
        else:
            diagnostics["network"]["ping_result"] = f"Failed (code {process.returncode})"
    except Exception as e:
        diagnostics["network"]["ping_result"] = f"Error: {str(e)}"
    
    logger.info(f"Diagnostics: Local IP={diagnostics['network']['local_ip']}, " 
                f"Device IP={DEVICE_IP}, Ping={diagnostics['network']['ping_result']}")
    
    return jsonify(diagnostics)

def cleanup():
    loop.close()

if __name__ == "__main__":
    import platform
    import sys
    
    logger.info("="*50)
    logger.info("Starting Tapo P110 Controller App")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Device IP: {DEVICE_IP}")
    logger.info("="*50)
    
    try:
        logger.info("Initializing device connection...")
        if loop.run_until_complete(initialize_device()):
            logger.info("Device initialized successfully")
        else:
            logger.warning("Failed to initialize device, app will run in offline mode")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        logger.warning("Running in offline mode")
        
    try:
        logger.info("Starting Flask server on 0.0.0.0:5000")
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        logger.info("Shutting down and cleaning up resources")
        cleanup()