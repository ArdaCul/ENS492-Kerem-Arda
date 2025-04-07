import asyncio
import logging
import os
from functools import wraps

from flask import Flask, jsonify, request, render_template
from tapo import ApiClient

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)

# Tapo credentials and device configuration
TAPO_USERNAME = os.environ.get("TAPO_USERNAME", "your_tapo_username")
TAPO_PASSWORD = os.environ.get("TAPO_PASSWORD", "your_tapo_password")
DEVICE_IP = os.environ.get("DEVICE_IP", "172.20.10.2")  # Updated with your device IP

# Global variable for device (will be set in initialize_device())
device = None
client = None

def async_action(f):
    """Decorator to run async functions in synchronous Flask routes"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

@async_action
async def initialize_device():
    """Initialize and connect to the Tapo P110 device"""
    global device, client
    try:
        client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
        device = await client.p110(DEVICE_IP)
        logger.info(f"Successfully connected to Tapo P110 at {DEVICE_IP}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to device: {str(e)}")
        return False

@app.route('/')
def index():
    """Render the web interface"""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
@async_action
async def get_status():
    """Get the current status of the device"""
    global device
    
    if not device:
        if not await initialize_device():
            return jsonify({"error": "Device not connected"}), 503
    
    try:
        # Get device info
        device_info = await device.get_device_info()
        
        # Convert the object to dictionary by examining its __dict__ or dir()
        # Try different attribute names based on the Tapo library implementation
        try:
            status = {
                "device_id": str(getattr(device_info, "device_id", "")),
                "device_name": str(getattr(device_info, "nickname", getattr(device_info, "name", "Tapo P110"))),
                "is_on": bool(getattr(device_info, "device_on", getattr(device_info, "on", False))),
                "on_time": int(getattr(device_info, "on_time", 0)),
                "overheated": bool(getattr(device_info, "overheated", False)),
                "firmware_version": str(getattr(device_info, "fw_ver", getattr(device_info, "firmware_version", ""))),
                "model": str(getattr(device_info, "model", "P110")),
                "device_type": str(getattr(device_info, "type", ""))
            }
        except Exception as e:
            logger.warning(f"Error extracting device info attributes: {str(e)}")
            # Fallback to a more generic approach
            attrs = dir(device_info)
            status = {}
            for attr in attrs:
                if not attr.startswith("_"):  # Skip private attributes
                    try:
                        value = getattr(device_info, attr)
                        if not callable(value):  # Skip methods
                            status[attr] = value
                    except Exception:
                        pass
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Failed to get device status: {str(e)}")
        return jsonify({"error": f"Failed to get device status: {str(e)}"}), 500

@app.route('/api/power/<state>', methods=['POST'])
@async_action
async def set_power(state):
    """Turn the device on or off"""
    global device
    
    if not device:
        if not await initialize_device():
            return jsonify({"error": "Device not connected"}), 503
    
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
        return jsonify({"error": f"Failed to set power state: {str(e)}"}), 500

@app.route('/api/energy', methods=['GET'])
@async_action
async def get_energy():
    """Get energy usage data from the device"""
    global device
    
    if not device:
        if not await initialize_device():
            return jsonify({"error": "Device not connected"}), 503
    
    try:
        # Get current power usage - handle it as a custom object
        current_power_obj = await device.get_current_power()
        logger.info(f"Current power type: {type(current_power_obj)}")
        
        # Extract the numeric value from the current power object
        if hasattr(current_power_obj, "power"):
            current_power = float(current_power_obj.power)
        elif hasattr(current_power_obj, "current_power"):
            current_power = float(current_power_obj.current_power)
        else:
            # If we can't find the specific attribute, try converting to float directly
            try:
                current_power = float(current_power_obj)
            except (TypeError, ValueError):
                current_power = 0.0
                logger.warning(f"Could not extract current power value from {current_power_obj}")
        
        # Get energy usage data
        energy_data = await device.get_energy_usage()
        
        # Extract energy values, handling different possible attribute names
        result = {
            "current_power_watts": current_power,
            "today_energy_kwh": float(getattr(energy_data, "today_energy", getattr(energy_data, "energy_today", 0.0))),
            "month_energy_kwh": float(getattr(energy_data, "month_energy", getattr(energy_data, "energy_month", 0.0))),
            "today_runtime": int(getattr(energy_data, "today_runtime", getattr(energy_data, "runtime_today", 0))),
            "month_runtime": int(getattr(energy_data, "month_runtime", getattr(energy_data, "runtime_month", 0)))
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to get energy data: {str(e)}")
        return jsonify({"error": f"Failed to get energy data: {str(e)}"}), 500

@app.route('/api/device-raw', methods=['GET'])
@async_action
async def get_device_raw():
    """Get raw device info for debugging"""
    global device
    
    if not device:
        if not await initialize_device():
            return jsonify({"error": "Device not connected"}), 503
    
    try:
        # Get device info as JSON
        device_info = await device.get_device_info_json()
        return jsonify({"raw_device_info": device_info})
    except Exception as e:
        logger.error(f"Failed to get raw device info: {str(e)}")
        return jsonify({"error": f"Failed to get raw device info: {str(e)}"}), 500

if __name__ == "__main__":
    # Initialize device connection on startup
    if initialize_device():
        logger.info("Device initialized successfully")
    else:
        logger.warning("Failed to initialize device, will retry on API calls")
        
    # Start the Flask server
    app.run(host="0.0.0.0", port=5000, debug=True)
