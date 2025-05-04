import logging
import time
import asyncio
import threading
from typing import Dict, List, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Helper function to get event loop safely
def get_event_loop():
    """Get or create event loop safely."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        # If no event loop exists in this thread, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

# Decorator to handle async operations
def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        loop = get_event_loop()
        try:
            # Use ensure_future to properly handle coroutines
            if asyncio.iscoroutinefunction(f):
                future = asyncio.ensure_future(f(*args, **kwargs), loop=loop)
                return loop.run_until_complete(future)
            else:
                # If it's not a coroutine, just call it normally
                return f(*args, **kwargs)
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                # Create a new thread to run the coroutine
                import threading
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(lambda: asyncio.run(f(*args, **kwargs)))
                    return future.result()
            else:
                raise
    return wrapped

class DeviceManager:
    """Manages both real Tapo devices and mock devices"""
    
    def __init__(self, tapo_username: str, tapo_password: str, devices: Dict):
        self.tapo_username = tapo_username
        self.tapo_password = tapo_password
        self.devices = devices
        self.tapo_client = None
        self.last_connection_attempt = 0
        self.connection_attempts = 0
        self.max_attempts = 3
        self.cooldown_period = 30  # seconds
        self.last_error = None
        
        # Try to initialize Tapo client if credentials are provided
        if tapo_username and tapo_password:
            self._initialize_tapo_client()
    
    def _initialize_tapo_client(self):
        """Initialize the Tapo API client"""
        try:
            # Check if pytapo is installed
            try:
                import pytapo
                logger.info(f"pytapo library version: {pytapo.__version__ if hasattr(pytapo, '__version__') else 'unknown'}")
                logger.info(f"Available in pytapo: {dir(pytapo)}")
            except ImportError:
                logger.error("pytapo library is not installed. Please run: pip install pytapo")
                self.tapo_client = None
                return
                
            # Check different possible API structures
            try:
                # Try importing ApiClient (older versions)
                from pytapo import ApiClient
                logger.info("Found ApiClient class, initializing")
                self.tapo_client = ApiClient(self.tapo_username, self.tapo_password)
                logger.info("Initialized pytapo ApiClient successfully")
            except ImportError:
                try:
                    # Try TPLinkTapoApiClient (medium versions)
                    from pytapo import TPLinkTapoApiClient
                    logger.info("Found TPLinkTapoApiClient class, initializing")
                    self.tapo_client = TPLinkTapoApiClient(self.tapo_username, self.tapo_password)
                    logger.info("Initialized pytapo TPLinkTapoApiClient successfully")
                except ImportError:
                    # If neither works, check if we have Tapo class (newer versions)
                    if hasattr(pytapo, 'Tapo'):
                        logger.info("Found pytapo.Tapo class, using this for device control")
                        # We'll use this directly with each device
                        self.tapo_client = pytapo
                        logger.info("Using pytapo module for direct Tapo class access")
                    else:
                        logger.error("No compatible client classes found in pytapo")
                        self.tapo_client = None
                        
        except Exception as e:
            logger.error(f"Error initializing Tapo client: {str(e)}")
            logger.exception("Detailed exception stacktrace:")
            self.tapo_client = None
    
    def update_credentials(self, username: str, password: str):
        """Update Tapo account credentials"""
        self.tapo_username = username
        self.tapo_password = password
        self._initialize_tapo_client()
    
    def update_devices(self, devices: Dict):
        """Update the list of devices"""
        self.devices = devices
    
    @async_action
    async def get_device_status(self, device_id: str) -> Dict:
        """Get the status of a device (real or mock)"""
        # Check mock devices first
        for device in self.devices.get('mock_devices', []):
            if device['id'] == device_id:
                return {
                    'id': device['id'],
                    'name': device['name'],
                    'type': device['type'],
                    'is_on': device['is_on'],
                    'power': device['avg_power'] if device['is_on'] else 0,
                    'dimming_level': device.get('dimming_level', 100) if device.get('is_dimmable', False) else None
                }
        
        # Check real devices
        for device in self.devices.get('real_devices', []):
            if device['id'] == device_id:
                tapo_device = await self._get_tapo_device(device['ip'])
                
                if tapo_device:
                    try:
                        device_info = await tapo_device.get_device_info()
                        return {
                            'id': device['id'],
                            'name': device['name'],
                            'type': device['type'],
                            'is_on': getattr(device_info, 'device_on', False),
                            'power': getattr(device_info, 'current_power', 0),
                            'dimming_level': getattr(device_info, 'brightness', 100) if hasattr(device_info, 'brightness') else None
                        }
                    except Exception as e:
                        logger.error(f"Error getting device info: {str(e)}")
                        
                # Fallback to stored state if Tapo communication fails
                return {
                    'id': device['id'],
                    'name': device['name'],
                    'type': device['type'],
                    'is_on': device.get('is_on', False),
                    'power': 0,  # We don't know without API
                    'dimming_level': device.get('dimming_level', 100)
                }
        
        return {'error': f"Device {device_id} not found"}
    
    @async_action
    async def control_device(self, device_id: str, action: str, value: Any) -> Dict:
        """Control a device (turn on/off, adjust brightness, etc.)"""
        # Control mock devices
        for device in self.devices.get('mock_devices', []):
            if device['id'] == device_id:
                if action == 'power':
                    device['is_on'] = bool(value)
                    logger.info(f"Set mock device {device['name']} (ID: {device_id}) power to {value}")
                elif action == 'dimming' and device.get('is_dimmable', False):
                    device['dimming_level'] = int(value)
                    # If dimming is adjusted, ensure device is on
                    if int(value) > 0:
                        device['is_on'] = True
                    logger.info(f"Set mock device {device['name']} (ID: {device_id}) dimming level to {value}")
                
                return {'success': True, 'device': device}
        
        # Control real devices
        for device in self.devices.get('real_devices', []):
            if device['id'] == device_id:
                tapo_device = await self._get_tapo_device(device['ip'])
                if not tapo_device:
                    logger.error(f"Could not connect to device at {device['ip']}")
                    return {'error': f"Could not connect to device at {device['ip']}"}
                
                try:
                    if action == 'power':
                        if value:
                            await tapo_device.on()
                            logger.info(f"Device {device_id} turned ON successfully")
                        else:
                            await tapo_device.off()
                            logger.info(f"Device {device_id} turned OFF successfully")
                        device['is_on'] = bool(value)
                    elif action == 'dimming' and hasattr(tapo_device, 'set_brightness'):
                        # For real devices, if setting brightness, ensure device is on first
                        if not device.get('is_on', False) and int(value) > 0:
                            await tapo_device.on()
                            device['is_on'] = True
                            
                        await tapo_device.set_brightness(int(value))
                        device['dimming_level'] = int(value)
                    
                    return {'success': True, 'device': device}
                except Exception as e:
                    logger.error(f"Error controlling device {device_id}: {str(e)}")
                    return {'error': str(e)}
        
        return {'error': f"Device {device_id} not found"}
    
    @async_action
    async def get_all_devices_status(self) -> List[Dict]:
        """Get status of all devices"""
        all_devices = []
        
        # Get mock devices status
        for device in self.devices.get('mock_devices', []):
            all_devices.append({
                'id': device['id'],
                'name': device['name'],
                'type': device['type'],
                'is_on': device['is_on'],
                'power': device['avg_power'] if device['is_on'] else 0,
                'dimming_level': device.get('dimming_level', 100) if device.get('is_dimmable', False) else None,
                'device_type': 'mock'
            })
        
        # Get real devices status
        for device in self.devices.get('real_devices', []):
            device_status = {
                'id': device['id'],
                'name': device['name'],
                'type': device['type'],
                'is_on': device.get('is_on', False),
                'power': 0,
                'dimming_level': device.get('dimming_level', 100),
                'device_type': 'tapo'
            }
            
            tapo_device = await self._get_tapo_device(device['ip'])
            if tapo_device:
                try:
                    device_info = await tapo_device.get_device_info()
                    device_status['is_on'] = getattr(device_info, 'device_on', False)
                    device_status['power'] = getattr(device_info, 'current_power', 0)
                    if hasattr(device_info, 'brightness'):
                        device_status['dimming_level'] = device_info.brightness
                except Exception as e:
                    logger.error(f"Error getting status for device {device['id']}: {str(e)}")
            
            all_devices.append(device_status)
        
        return all_devices
    
    @async_action
    async def get_total_power_usage(self) -> float:
        """Get total power usage of all devices in watts"""
        total_power = 0.0
        
        # Add mock devices power
        for device in self.devices.get('mock_devices', []):
            if device['is_on']:
                power = device['avg_power']
                # Adjust for dimming if applicable
                if device.get('is_dimmable', False) and device.get('dimming_level') is not None:
                    dimming_level = device.get('dimming_level')
                    if isinstance(dimming_level, str):
                        dimming_level = int(dimming_level)
                    if dimming_level < 100:
                        power = power * (dimming_level / 100)
                total_power += power
        
        # Add real devices power
        for device in self.devices.get('real_devices', []):
            tapo_device = await self._get_tapo_device(device['ip'])
            if tapo_device:
                try:
                    device_info = await tapo_device.get_device_info()
                    if getattr(device_info, 'device_on', False):
                        power_info = await tapo_device.get_current_power()
                        total_power += getattr(power_info, 'power', 0)
                except Exception as e:
                    logger.error(f"Error getting power for device {device['id']}: {str(e)}")
                    # If we can't get real power, use average if device is known to be on
                    if device.get('is_on', False) and device.get('avg_power', 0) > 0:
                        total_power += device.get('avg_power', 0)
            elif device.get('is_on', False) and device.get('avg_power', 0) > 0:
                # If device connection failed but device is marked as on, use avg power
                total_power += device.get('avg_power', 0)
        
        return total_power
    
    async def _get_tapo_device(self, ip: str):
        """Get a Tapo device by IP"""
        if not self.tapo_client:
            logger.error(f"Tapo client not initialized when trying to connect to device at {ip}")
            return None
        
        current_time = time.time()
        
        # Check if we need to enforce cooldown period
        if self.connection_attempts >= self.max_attempts and current_time - self.last_connection_attempt < self.cooldown_period:
            logger.warning(f"Too many failed connection attempts, waiting for cooldown period to expire")
            return None
            
        try:
            logger.info(f"Attempting to connect to Tapo device at IP: {ip}")
            self.last_connection_attempt = current_time
            self.connection_attempts += 1
            
            # Different connection methods based on the library version
            if self.tapo_client == pytapo:
                # Modern pytapo with Tapo class
                try:
                    # Try with HTTPS first
                    logger.info(f"Trying HTTPS connection to {ip}")
                    device = pytapo.Tapo(ip, self.tapo_username, self.tapo_password)
                    logger.info(f"HTTPS connection to {ip} successful")
                    
                    # Reset connection attempts on success
                    self.connection_attempts = 0
                    self.last_error = None
                    return device
                except Exception as e1:
                    logger.warning(f"HTTPS connection failed: {str(e1)}")
                    # Try with HTTP
                    try:
                        logger.info(f"Trying HTTP connection to {ip}")
                        device = pytapo.Tapo(ip, self.tapo_username, self.tapo_password, use_https=False)
                        logger.info(f"HTTP connection to {ip} successful")
                        
                        # Reset connection attempts on success
                        self.connection_attempts = 0
                        self.last_error = None
                        return device
                    except Exception as e2:
                        logger.error(f"HTTP connection also failed: {str(e2)}")
                        self.last_error = str(e2)
                        return None
            
            # Older style with client.p110() method
            elif hasattr(self.tapo_client, 'p110'):
                logger.info(f"Using p110() method for {ip}")
                device = await self.tapo_client.p110(ip)
                logger.info(f"Successfully connected using p110() method")
                
                # Reset connection attempts on success
                self.connection_attempts = 0
                self.last_error = None
                return device
                
            # Medium style with get_device() method  
            elif hasattr(self.tapo_client, 'get_device'):
                logger.info(f"Using get_device() method for {ip}")
                device = await self.tapo_client.get_device(ip)
                logger.info(f"Successfully connected using get_device() method")
                
                # Reset connection attempts on success
                self.connection_attempts = 0
                self.last_error = None
                return device
                
            else:
                logger.error(f"No method found to connect to device at {ip}")
                self.last_error = "No suitable connection method found"
                return None
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error connecting to Tapo device at {ip}: {str(e)}")
            logger.exception("Detailed exception information:")
            return None
    
    def start_periodic_check(self):
        """Start a background thread to periodically check devices"""
        check_thread = threading.Thread(target=self._periodic_device_check, daemon=True)
        check_thread.start()
        logger.info("Started periodic device checking")
    
    def _periodic_device_check(self):
        """Periodically check all devices to maintain connection"""
        while True:
            try:
                # Get a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Check each real device
                for device in self.devices.get('real_devices', []):
                    try:
                        # Try to get the device
                        tapo_device = loop.run_until_complete(self._get_tapo_device(device['ip']))
                        if tapo_device:
                            # Get device info to keep connection alive
                            loop.run_until_complete(tapo_device.get_device_info())
                            logger.debug(f"Periodic check: Device {device['id']} is online")
                    except Exception as e:
                        logger.error(f"Error checking device {device['id']}: {str(e)}")
                
                # Clean up
                loop.close()
                
                # Wait before next check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in periodic device check: {str(e)}")
                time.sleep(120)  # Wait longer after error