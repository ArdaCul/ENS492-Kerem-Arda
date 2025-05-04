import logging
import time
import json
import os
from typing import Dict, List, Optional
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnergyManager:
    """Manages energy flows between grid, batteries, and devices"""
    
    # Battery modes
    BATTERY_IDLE = 'idle'
    BATTERY_CHARGING = 'charging'
    BATTERY_IN_USE = 'in_use'
    
    def __init__(self, config: Dict, device_manager):
        self.config = config
        self.device_manager = device_manager
        self.history_file = 'energy_history.json'
        
        # Initialize default values if not in config
        if 'grid_max_power' not in self.config:
            self.config['grid_max_power'] = 10000  # Default 10kW
            
        if 'home_battery_max_output' not in self.config:
            self.config['home_battery_max_output'] = 5000  # Default 5kW
            
        if 'home_battery_max_input' not in self.config:
            self.config['home_battery_max_input'] = 3500  # Default 3.5kW
            
        if 'car_battery_max_output' not in self.config:
            self.config['car_battery_max_output'] = 7500  # Default 7.5kW
            
        if 'car_battery_max_input' not in self.config:
            self.config['car_battery_max_input'] = 11000  # Default 11kW
            
        if 'home_battery_mode' not in self.config:
            self.config['home_battery_mode'] = self.BATTERY_IDLE
            
        if 'car_battery_mode' not in self.config:
            self.config['car_battery_mode'] = self.BATTERY_IDLE
            
        # Default priority (grid first, then home battery, then car)
        if 'power_priorities' not in self.config:
            self.config['power_priorities'] = ['grid', 'home_battery', 'car_battery']
        
        # Load or initialize history
        self.history = self._load_history()
        
        # Start time for simulation
        self.start_time = time.time()
        self.last_update = self.start_time
        
        # Flag to prevent recursion
        self._updating = False
    
    def update_config(self, config: Dict):
        """Update configuration"""
        self.config = config
        
        # Ensure required fields are present
        if 'grid_max_power' not in self.config:
            self.config['grid_max_power'] = 10000
            
        if 'home_battery_max_output' not in self.config:
            self.config['home_battery_max_output'] = 5000
            
        if 'home_battery_max_input' not in self.config:
            self.config['home_battery_max_input'] = 3500
            
        if 'car_battery_max_output' not in self.config:
            self.config['car_battery_max_output'] = 7500
            
        if 'car_battery_max_input' not in self.config:
            self.config['car_battery_max_input'] = 11000
            
        if 'home_battery_mode' not in self.config:
            self.config['home_battery_mode'] = self.BATTERY_IDLE
            
        if 'car_battery_mode' not in self.config:
            self.config['car_battery_mode'] = self.BATTERY_IDLE
            
        # Default priority if not set
        if 'power_priorities' not in self.config:
            self.config['power_priorities'] = ['grid', 'home_battery', 'car_battery']
    
    def get_status(self) -> Dict:
        """Get current energy status"""
        # Update simulation state if not already updating
        if not self._updating:
            self._update_simulation()
        
        # Get total power usage from devices
        total_device_power = self.device_manager.get_total_power_usage()
        print(f"DEBUG: Total device power usage: {total_device_power}W")
        
        
        # Calculate power from each source based on priorities and constraints
        grid_power, home_battery_power, car_battery_power = self._calculate_power_distribution(total_device_power)
        
        # Set default values for disabled components
        grid_enabled = self.config.get('grid_enabled', True)
        home_battery_enabled = self.config.get('home_battery_enabled', True)
        car_battery_enabled = self.config.get('car_battery_enabled', False)
        
        # Default values for disabled components
        electricity_rate = 0
        home_battery_level = 0
        car_battery_level = 0
        home_battery_capacity = 0
        car_battery_capacity = 0
        car_connected = False
        
        # Get grid values
        if grid_enabled:
            electricity_rate = self.config.get('electricity_rate', 0.15)
            grid_max_power = self.config.get('grid_max_power', 10000)
        else:
            grid_power = 0
            grid_max_power = 0
        
        # Get home battery values
        if home_battery_enabled:
            home_battery_capacity = self.config.get('home_battery_capacity', 10)
            home_battery_level = self.config.get('home_battery_level', 50)
            home_battery_max_output = self.config.get('home_battery_max_output', 5000)
            home_battery_max_input = self.config.get('home_battery_max_input', 3500)
            home_battery_mode = self.config.get('home_battery_mode', self.BATTERY_IDLE)
            
            # If not in use, no power
            if home_battery_mode != self.BATTERY_IN_USE:
                home_battery_power = 0
        else:
            home_battery_power = 0
            home_battery_capacity = 0
            home_battery_level = 0
            home_battery_max_output = 0
            home_battery_max_input = 0
            home_battery_mode = self.BATTERY_IDLE
        
        # Get car battery values
        if car_battery_enabled:
            car_battery_capacity = self.config.get('car_battery_capacity', 75)
            car_battery_level = self.config.get('car_battery_level', 80)
            car_battery_max_output = self.config.get('car_battery_max_output', 7500)
            car_battery_max_input = self.config.get('car_battery_max_input', 11000)
            car_connected = self.config.get('car_connected', False)
            car_battery_mode = self.config.get('car_battery_mode', self.BATTERY_IDLE)
            
            # If not connected or not in use, no power
            if not car_connected or car_battery_mode != self.BATTERY_IN_USE:
                car_battery_power = 0
        else:
            car_battery_power = 0
            car_battery_capacity = 0
            car_battery_level = 0
            car_battery_max_output = 0
            car_battery_max_input = 0
            car_connected = False
            car_battery_mode = self.BATTERY_IDLE
        
        # Calculate estimated daily cost
        estimated_daily_cost = (grid_power * 24 / 1000) * electricity_rate if grid_enabled else 0
        
        return {
            'timestamp': time.time(),
            'total_power_usage': total_device_power,  # In watts
            'grid_power': grid_power,  # In watts
            'home_battery_power': home_battery_power,  # In watts
            'car_battery_power': car_battery_power,  # In watts
            'home_battery_level': home_battery_level,  # In percent
            'car_battery_level': car_battery_level,  # In percent
            'grid_enabled': grid_enabled,
            'home_battery_enabled': home_battery_enabled,
            'car_battery_enabled': car_battery_enabled,
            'car_connected': car_connected,
            'electricity_rate': electricity_rate,  # In $/kWh
            'estimated_daily_cost': estimated_daily_cost,  # Daily cost in $
            'home_battery_capacity': home_battery_capacity,  # In kWh
            'car_battery_capacity': car_battery_capacity,  # In kWh
            'grid_max_power': grid_max_power,  # In watts
            'home_battery_max_output': home_battery_max_output,  # In watts
            'home_battery_max_input': home_battery_max_input,  # In watts
            'car_battery_max_output': car_battery_max_output,  # In watts
            'car_battery_max_input': car_battery_max_input,  # In watts
            'home_battery_mode': home_battery_mode,  # idle, charging, in_use
            'car_battery_mode': car_battery_mode,  # idle, charging, in_use
            'power_priorities': self.config.get('power_priorities', ['grid', 'home_battery', 'car_battery'])
        }
    
    def _calculate_power_distribution(self, total_power_watts: float) -> tuple:
        """Calculate power distribution based on priorities and constraints"""
        # Get priorities
        priorities = self.config.get('power_priorities', ['grid', 'home_battery', 'car_battery'])
        
        # Get enabled status
        grid_enabled = self.config.get('grid_enabled', True)
        home_battery_enabled = self.config.get('home_battery_enabled', True)
        car_battery_enabled = self.config.get('car_battery_enabled', False)
        car_connected = self.config.get('car_connected', False)
        
        # Get battery modes
        home_battery_mode = self.config.get('home_battery_mode', self.BATTERY_IDLE)
        car_battery_mode = self.config.get('car_battery_mode', self.BATTERY_IDLE)
        
        # Initialize power values
        grid_power = 0
        home_battery_power = 0
        car_battery_power = 0
        
        # Check which sources are available
        sources_available = {}
        
        # Grid availability
        sources_available['grid'] = grid_enabled
        
        # Home battery availability
        sources_available['home_battery'] = (
            home_battery_enabled and
            home_battery_mode == self.BATTERY_IN_USE and
            self.config.get('home_battery_level', 0) > 0
        )
        
        # Car battery availability
        sources_available['car_battery'] = (
            car_battery_enabled and
            car_connected and
            car_battery_mode == self.BATTERY_IN_USE and
            self.config.get('car_battery_level', 0) > 0
        )
        
        # Track remaining power to be supplied
        remaining_power = total_power_watts
        
        # Go through priorities and allocate power
        for source in priorities:
            if remaining_power <= 0:
                break
                
            if not sources_available.get(source, False):
                continue
                
            if source == 'grid':
                # Grid power is limited by max capacity
                max_power = self.config.get('grid_max_power', 10000)
                grid_power = min(remaining_power, max_power)
                remaining_power -= grid_power
                
            elif source == 'home_battery':
                # Home battery power is limited by battery level and max output
                max_output = self.config.get('home_battery_max_output', 5000)
                
                # Further limit based on battery level
                battery_level = self.config.get('home_battery_level', 50)
                if battery_level <= 10:  # Below 10% limit output
                    max_output = max_output * (battery_level / 10)
                
                home_battery_power = min(remaining_power, max_output)
                remaining_power -= home_battery_power
                
            elif source == 'car_battery':
                # Car battery power is limited by battery level and max output
                max_output = self.config.get('car_battery_max_output', 7500)
                
                # Further limit based on battery level
                battery_level = self.config.get('car_battery_level', 80)
                if battery_level <= 20:  # Below 20% limit output
                    max_output = max_output * (battery_level / 20)
                
                car_battery_power = min(remaining_power, max_output)
                remaining_power -= car_battery_power
        
        # Double check if battery modes are respected
        home_battery_mode = self.config.get('home_battery_mode', self.BATTERY_IDLE)
        if home_battery_mode != self.BATTERY_IN_USE:
            home_battery_power = 0
            
        car_battery_mode = self.config.get('car_battery_mode', self.BATTERY_IDLE)
        car_connected = self.config.get('car_connected', False)
        if car_battery_mode != self.BATTERY_IN_USE or not car_connected:
            car_battery_power = 0
            
        print(f"DEBUG: Power distribution - Total: {total_power_watts}W, Grid: {grid_power}W, Home: {home_battery_power}W, Car: {car_battery_power}W")
        
        return grid_power, home_battery_power, car_battery_power
    
    def update_power_priority(self, priorities: List[str]) -> bool:
        """Update power priority order"""
        # Validate priorities
        valid_sources = ['grid', 'home_battery', 'car_battery']
        
        # Check if all required sources are included
        if len(priorities) != 3 or not all(source in valid_sources for source in priorities):
            return False
            
        # Check for duplicates
        if len(set(priorities)) != 3:
            return False
            
        # Update priorities in config
        self.config['power_priorities'] = priorities
        
        return True
    
    def set_battery_mode(self, battery_type: str, mode: str) -> bool:
        """Set the mode of a battery (idle, charging, in_use)"""
        valid_modes = [self.BATTERY_IDLE, self.BATTERY_CHARGING, self.BATTERY_IN_USE]
        
        if mode not in valid_modes:
            return False
        
        if battery_type == 'home':
            self.config['home_battery_mode'] = mode
            return True
        elif battery_type == 'car':
            self.config['car_battery_mode'] = mode
            return True
        
        return False
    
    def get_history(self, period: str = 'day') -> Dict:
        """Get energy usage history"""
        # Ensure simulation is up to date
        if not self._updating:
            self._update_simulation()
        
        # Get the history data
        history_data = self.history
        
        # Filter based on period
        now = time.time()
        if period == 'day':
            # Last 24 hours
            start_time = now - (24 * 60 * 60)
            filtered_data = [entry for entry in history_data if entry['timestamp'] >= start_time]
        elif period == 'week':
            # Last 7 days
            start_time = now - (7 * 24 * 60 * 60)
            filtered_data = [entry for entry in history_data if entry['timestamp'] >= start_time]
        elif period == 'month':
            # Last 30 days
            start_time = now - (30 * 24 * 60 * 60)
            filtered_data = [entry for entry in history_data if entry['timestamp'] >= start_time]
        else:
            filtered_data = history_data
        
        # Process data for charts
        times = [entry['timestamp'] for entry in filtered_data]
        total_usage = [entry['total_power_usage'] for entry in filtered_data]
        grid_power = [entry['grid_power'] for entry in filtered_data]
        home_battery_power = [entry['home_battery_power'] for entry in filtered_data]
        car_battery_power = [entry['car_battery_power'] for entry in filtered_data]
        
        # Calculate totals
        if filtered_data:
            avg_power = sum(total_usage) / len(total_usage)
            max_power = max(total_usage) if total_usage else 0
            
            # Calculate kWh
            duration_hours = (now - start_time) / 3600
            total_kwh = sum(total_usage) * duration_hours / 1000 / len(filtered_data)
            grid_kwh = sum(grid_power) * duration_hours / 1000 / len(filtered_data)
            home_battery_kwh = sum(home_battery_power) * duration_hours / 1000 / len(filtered_data)
            car_battery_kwh = sum(car_battery_power) * duration_hours / 1000 / len(filtered_data)
            
            # Calculate cost
            electricity_rate = self.config.get('electricity_rate', 0.15) if self.config.get('grid_enabled', True) else 0
            total_cost = grid_kwh * electricity_rate
        else:
            avg_power = 0
            max_power = 0
            total_kwh = 0
            grid_kwh = 0
            home_battery_kwh = 0
            car_battery_kwh = 0
            total_cost = 0
        
        return {
            'period': period,
            'timestamps': times,
            'total_usage': total_usage,
            'grid_power': grid_power,
            'home_battery_power': home_battery_power,
            'car_battery_power': car_battery_power,
            'summary': {
                'avg_power': avg_power,
                'max_power': max_power,
                'total_kwh': total_kwh,
                'grid_kwh': grid_kwh,
                'home_battery_kwh': home_battery_kwh,
                'car_battery_kwh': car_battery_kwh,
                'total_cost': total_cost
            }
        }
    
    def _update_simulation(self):
        """Update simulation state based on time elapsed"""
        # Set flag to prevent recursion
        self._updating = True
        
        current_time = time.time()
        elapsed_time = current_time - self.last_update
        
        if elapsed_time < 60:  # Only update every minute
            self._updating = False
            return
            
        # Get current status
        total_device_power = self.device_manager.get_total_power_usage()
        
        # Update battery levels based on usage/charging
        self._update_battery_levels(elapsed_time, total_device_power)
        
        # Record current state in history
        self._record_history_safely()
        
        # Update last update time
        self.last_update = current_time
        
        # Reset flag
        self._updating = False
    
    def _update_battery_levels(self, elapsed_time_seconds, total_power_watts):
        """Update battery levels based on usage or charging"""
        # Convert elapsed time to hours
        elapsed_hours = elapsed_time_seconds / 3600
        
        # Home battery simulation
        if self.config.get('home_battery_enabled', True):
            home_battery_capacity_kwh = self.config.get('home_battery_capacity', 10)
            home_battery_level = self.config.get('home_battery_level', 50)
            home_battery_mode = self.config.get('home_battery_mode', self.BATTERY_IDLE)
            
            if home_battery_mode == self.BATTERY_IN_USE:
                # Calculate energy flow for home battery based on priorities
                grid_power, home_battery_power, car_battery_power = self._calculate_power_distribution(total_power_watts)
                
                # Convert to kWh
                energy_change_kwh = home_battery_power * elapsed_hours / 1000
                
                # Calculate percentage change (discharge)
                percentage_change = energy_change_kwh / home_battery_capacity_kwh * 100
                
                # Update battery level (discharge)
                home_battery_level = max(0, home_battery_level - percentage_change)
                
            elif home_battery_mode == self.BATTERY_CHARGING:
                # Calculate charging power (limited by max input)
                charging_power = min(self.config.get('home_battery_max_input', 3500), 
                                   self.config.get('grid_max_power', 10000))
                
                # Convert to kWh
                energy_change_kwh = charging_power * elapsed_hours / 1000
                
                # Calculate percentage change (charge)
                percentage_change = energy_change_kwh / home_battery_capacity_kwh * 100
                
                # Update battery level (charge)
                home_battery_level = min(100, home_battery_level + percentage_change)
            
            # Update config
            self.config['home_battery_level'] = home_battery_level
        
        # Car battery simulation
        if self.config.get('car_battery_enabled', False) and self.config.get('car_connected', False):
            car_battery_capacity_kwh = self.config.get('car_battery_capacity', 75)
            car_battery_level = self.config.get('car_battery_level', 80)
            car_battery_mode = self.config.get('car_battery_mode', self.BATTERY_IDLE)
            
            if car_battery_mode == self.BATTERY_IN_USE:
                # Calculate energy flow for car battery based on priorities
                grid_power, home_battery_power, car_battery_power = self._calculate_power_distribution(total_power_watts)
                
                # Convert to kWh
                energy_change_kwh = car_battery_power * elapsed_hours / 1000
                
                # Calculate percentage change (discharge)
                percentage_change = energy_change_kwh / car_battery_capacity_kwh * 100
                
                # Update battery level (discharge)
                car_battery_level = max(0, car_battery_level - percentage_change)
                
            elif car_battery_mode == self.BATTERY_CHARGING:
                # Calculate charging power (limited by max input)
                charging_power = min(self.config.get('car_battery_max_input', 11000), 
                                   self.config.get('grid_max_power', 10000))
                
                # Convert to kWh
                energy_change_kwh = charging_power * elapsed_hours / 1000
                
                # Calculate percentage change (charge)
                percentage_change = energy_change_kwh / car_battery_capacity_kwh * 100
                
                # Update battery level (charge)
                car_battery_level = min(100, car_battery_level + percentage_change)
            
            # Update config
            self.config['car_battery_level'] = car_battery_level
        
        # Simulate random reconnection of car (about once per day)
        if self.config.get('car_battery_enabled', False) and random.random() < (elapsed_hours / 24 / 7):  # Approximately once per week
            self.config['car_connected'] = not self.config.get('car_connected', False)
            
            # If car just connected, give it a random battery level
            if self.config['car_connected']:
                self.config['car_battery_level'] = random.uniform(30, 90)
                # Set car battery to idle mode when connected
                self.config['car_battery_mode'] = self.BATTERY_IDLE
    
    def _record_history_safely(self):
        """Record current energy status in history without recursion"""
        # Calculate energy status directly without calling get_status()
        total_device_power = self.device_manager.get_total_power_usage()
        
        # Calculate power distribution
        grid_power, home_battery_power, car_battery_power = self._calculate_power_distribution(total_device_power)
        
        # Get values based on configuration
        grid_enabled = self.config.get('grid_enabled', True)
        home_battery_enabled = self.config.get('home_battery_enabled', True)
        car_battery_enabled = self.config.get('car_battery_enabled', False)
        car_connected = self.config.get('car_connected', False)
        home_battery_level = self.config.get('home_battery_level', 50) if home_battery_enabled else 0
        car_battery_level = self.config.get('car_battery_level', 80) if car_battery_enabled else 0
        
        # Create status entry
        status = {
            'timestamp': time.time(),
            'total_power_usage': total_device_power,
            'grid_power': grid_power,
            'home_battery_power': home_battery_power,
            'car_battery_power': car_battery_power,
            'home_battery_level': home_battery_level,
            'car_battery_level': car_battery_level,
            'grid_enabled': grid_enabled,
            'home_battery_enabled': home_battery_enabled,
            'car_battery_enabled': car_battery_enabled,
            'car_connected': car_connected
        }
        
        # Add to history
        self.history.append(status)
        
        # Limit history size (keep last 30 days)
        thirty_days_ago = time.time() - (30 * 24 * 60 * 60)
        self.history = [entry for entry in self.history if entry['timestamp'] >= thirty_days_ago]
        
        # Save history to file periodically (every hour)
        if random.random() < 0.01:  # Approximately once per 100 updates
            self._save_history()
    
    def _load_history(self):
        """Load energy history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading history: {str(e)}")
        
        # If file doesn't exist or error occurs, initialize with some sample data
        return self._initialize_sample_history()
    
    def _save_history(self):
        """Save energy history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving history: {str(e)}")
    
    def _initialize_sample_history(self):
        """Initialize sample history data"""
        history = []
        
        # Create sample data for last 7 days
        now = time.time()
        day_in_seconds = 24 * 60 * 60
        
        for day in range(7):
            day_start = now - ((7 - day) * day_in_seconds)
            
            # Add data points every hour
            for hour in range(24):
                timestamp = day_start + (hour * 60 * 60)
                
                # Base load varies by time of day
                base_load = 100  # 100W base load
                
                # Add morning peak (7-9am)
                if 7 <= hour <= 9:
                    base_load += random.uniform(200, 500)
                
                # Add evening peak (6-10pm)
                if 18 <= hour <= 22:
                    base_load += random.uniform(300, 700)
                
                # Add random variation
                total_power = base_load + random.uniform(-50, 50)
                
                # Calculate source breakdown
                grid_power = total_power * 0.7
                home_battery_power = total_power * 0.2
                car_battery_power = total_power * 0.1
                
                entry = {
                    'timestamp': timestamp,
                    'total_power_usage': total_power,
                    'grid_power': grid_power,
                    'home_battery_power': home_battery_power,
                    'car_battery_power': car_battery_power,
                    'home_battery_level': 50 - (day * 5) + (hour % 10),  # Simulate charging/discharging
                    'car_battery_level': 80 - (day * 3) + (hour % 15),
                    'grid_enabled': True,
                    'home_battery_enabled': True,
                    'car_battery_enabled': True,
                    'car_connected': (day % 2 == 0)  # Car connected every other day
                }
                
                history.append(entry)
        
        return history