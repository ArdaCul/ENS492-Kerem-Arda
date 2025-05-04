// God Mode JavaScript for simulation controls

document.addEventListener('DOMContentLoaded', function() {
    // Load initial config
    loadConfig();
    
    // Set up event listeners
    setupEventListeners();
    
    // Log simulation start
    logSimulation('Simulation control panel initialized');
});

function setupEventListeners() {
    // Grid controls
    document.getElementById('gridEnabledSwitch').addEventListener('change', function() {
        updateConfig({ 'grid_enabled': this.checked });
        document.getElementById('gridStatusLabel').textContent = this.checked ? 'Connected' : 'Disconnected';
        logSimulation(`Grid ${this.checked ? 'connected' : 'disconnected'}`);
    });
    
    document.getElementById('electricityRateInput').addEventListener('change', function() {
        updateConfig({ 'electricity_rate': parseFloat(this.value) });
        logSimulation(`Electricity rate updated to $${this.value}/kWh`);
    });
    
    document.getElementById('gridMaxPowerInput').addEventListener('change', function() {
        updateConfig({ 'grid_max_power': parseFloat(this.value) });
        logSimulation(`Grid maximum power updated to ${this.value} W`);
    });
    
    document.getElementById('simulateOutageBtn').addEventListener('click', function() {
        // Disable grid for 30 seconds in simulation time
        updateConfig({ 'grid_enabled': false });
        document.getElementById('gridEnabledSwitch').checked = false;
        document.getElementById('gridStatusLabel').textContent = 'Disconnected';
        
        logSimulation('Grid outage simulation started (30 min)');
        
        // Auto-restore after 30 seconds
        setTimeout(() => {
            updateConfig({ 'grid_enabled': true });
            document.getElementById('gridEnabledSwitch').checked = true;
            document.getElementById('gridStatusLabel').textContent = 'Connected';
            logSimulation('Grid power restored after outage');
        }, 30000);
    });
    
    // Home battery controls
    document.getElementById('homeBatteryEnabledSwitch').addEventListener('change', function() {
        updateConfig({ 'home_battery_enabled': this.checked });
        document.getElementById('homeBatteryStatusLabel').textContent = this.checked ? 'Enabled' : 'Disabled';
        logSimulation(`Home battery ${this.checked ? 'enabled' : 'disabled'}`);
        
        // Enable/disable related controls
        const controls = ['homeBatteryCapacityInput', 'homeBatteryMaxOutputInput', 
                          'homeBatteryMaxInputInput', 'homeBatteryLevelInput', 
                          'simulateBatteryChargeBtn', 'simulateBatteryDischargeBtn'];
        
        controls.forEach(id => {
            document.getElementById(id).disabled = !this.checked;
        });
        
        document.querySelectorAll('input[name="homeBatteryMode"]').forEach(radio => {
            radio.disabled = !this.checked;
        });
    });
    
    document.getElementById('homeBatteryCapacityInput').addEventListener('change', function() {
        updateConfig({ 'home_battery_capacity': parseFloat(this.value) });
        logSimulation(`Home battery capacity updated to ${this.value} kWh`);
    });
    
    document.getElementById('homeBatteryMaxOutputInput').addEventListener('change', function() {
        updateConfig({ 'home_battery_max_output': parseFloat(this.value) });
        logSimulation(`Home battery maximum output updated to ${this.value} W`);
    });
    
    document.getElementById('homeBatteryMaxInputInput').addEventListener('change', function() {
        updateConfig({ 'home_battery_max_input': parseFloat(this.value) });
        logSimulation(`Home battery maximum input updated to ${this.value} W`);
    });
    
    document.getElementById('homeBatteryLevelInput').addEventListener('input', function() {
        document.getElementById('homeBatteryLevelValue').textContent = `${this.value}%`;
    });
    
    document.getElementById('homeBatteryLevelInput').addEventListener('change', function() {
        updateConfig({ 'home_battery_level': parseInt(this.value) });
        logSimulation(`Home battery level set to ${this.value}%`);
    });
    
    // Home battery mode control
    document.querySelectorAll('input[name="homeBatteryMode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            updateConfig({ 'home_battery_mode': this.value });
            logSimulation(`Home battery mode set to ${this.value}`);
        });
    });
    
    document.getElementById('simulateBatteryChargeBtn').addEventListener('click', function() {
        updateConfig({ 'home_battery_level': 100 });
        document.getElementById('homeBatteryLevelInput').value = 100;
        document.getElementById('homeBatteryLevelValue').textContent = '100%';
        logSimulation('Home battery charged to 100%');
    });
    
    document.getElementById('simulateBatteryDischargeBtn').addEventListener('click', function() {
        updateConfig({ 'home_battery_level': 10 });
        document.getElementById('homeBatteryLevelInput').value = 10;
        document.getElementById('homeBatteryLevelValue').textContent = '10%';
        logSimulation('Home battery discharged to 10%');
    });
    
    // Car battery controls
    document.getElementById('carBatteryEnabledSwitch').addEventListener('change', function() {
        updateConfig({ 'car_battery_enabled': this.checked });
        document.getElementById('carBatteryStatusLabel').textContent = this.checked ? 'Enabled' : 'Disabled';
        logSimulation(`EV battery ${this.checked ? 'enabled' : 'disabled'}`);
        
        // Enable/disable related controls
        const controls = ['carConnectedSwitch', 'carBatteryCapacityInput', 'carBatteryMaxOutputInput', 
                          'carBatteryMaxInputInput', 'carBatteryLevelInput', 'simulateCarTripBtn'];
        
        controls.forEach(id => {
            document.getElementById(id).disabled = !this.checked;
        });
        
        document.querySelectorAll('input[name="carBatteryMode"]').forEach(radio => {
            radio.disabled = !this.checked;
        });
        
        // If disabling, also ensure car is disconnected
        if (!this.checked) {
            document.getElementById('carConnectedSwitch').checked = false;
            document.getElementById('carConnectedStatusLabel').textContent = 'Disconnected';
            updateConfig({ 'car_connected': false });
        }
    });
    
    document.getElementById('carConnectedSwitch').addEventListener('change', function() {
        updateConfig({ 'car_connected': this.checked });
        document.getElementById('carConnectedStatusLabel').textContent = this.checked ? 'Connected' : 'Disconnected';
        logSimulation(`Car ${this.checked ? 'connected to home' : 'disconnected from home'}`);
    });
    
    document.getElementById('carBatteryCapacityInput').addEventListener('change', function() {
        updateConfig({ 'car_battery_capacity': parseFloat(this.value) });
        logSimulation(`EV battery capacity updated to ${this.value} kWh`);
    });
    
    document.getElementById('carBatteryMaxOutputInput').addEventListener('change', function() {
        updateConfig({ 'car_battery_max_output': parseFloat(this.value) });
        logSimulation(`EV battery maximum output updated to ${this.value} W`);
    });
    
    document.getElementById('carBatteryMaxInputInput').addEventListener('change', function() {
        updateConfig({ 'car_battery_max_input': parseFloat(this.value) });
        logSimulation(`EV battery maximum input updated to ${this.value} W`);
    });
    
    document.getElementById('carBatteryLevelInput').addEventListener('input', function() {
        document.getElementById('carBatteryLevelValue').textContent = `${this.value}%`;
    });
    
    document.getElementById('carBatteryLevelInput').addEventListener('change', function() {
        updateConfig({ 'car_battery_level': parseInt(this.value) });
        logSimulation(`EV battery level set to ${this.value}%`);
    });
    
    // Car battery mode control
    document.querySelectorAll('input[name="carBatteryMode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            updateConfig({ 'car_battery_mode': this.value });
            logSimulation(`EV battery mode set to ${this.value}`);
        });
    });
    
    document.getElementById('simulateCarTripBtn').addEventListener('click', function() {
        // Disconnect car and reduce battery level
        updateConfig({
            'car_connected': false,
            'car_battery_level': Math.max(20, parseInt(document.getElementById('carBatteryLevelInput').value) - 30)
        });
        
        document.getElementById('carConnectedSwitch').checked = false;
        document.getElementById('carConnectedStatusLabel').textContent = 'Disconnected';
        
        const newLevel = Math.max(20, parseInt(document.getElementById('carBatteryLevelInput').value) - 30);
        document.getElementById('carBatteryLevelInput').value = newLevel;
        document.getElementById('carBatteryLevelValue').textContent = `${newLevel}%`;
        
        logSimulation(`Simulated car trip: EV battery reduced to ${newLevel}%`);
    });
    

    
    // Load simulation buttons
    document.getElementById('simulateDayloadBtn').addEventListener('click', function() {
        logSimulation('Simulating typical day load pattern...');
        // This would set up a sequence of load changes over time
        alert('Simulation started: Device loads will change throughout the day to simulate typical usage patterns.');
    });
    
    document.getElementById('simulateHighLoadBtn').addEventListener('click', function() {
        logSimulation('Simulating high load period (2 hours)...');
        // This would simulate high load by turning on power-hungry devices
        turnOnHighLoadDevices();
    });
    
    document.getElementById('simulateLowLoadBtn').addEventListener('click', function() {
        logSimulation('Simulating low load period (night)...');
        // This would simulate low load by turning off most devices
        turnOffMostDevices();
    });
    
    document.getElementById('simulateRandomEventsBtn').addEventListener('click', function() {
        logSimulation('Simulating random events...');
        // This would create random events like device failures, power spikes, etc.
        simulateRandomEvents();
    });
    
    // Clear log button
    document.getElementById('clearLogBtn').addEventListener('click', function() {
        document.getElementById('simulationLog').textContent = 'Simulation log cleared.';
    });
}

function loadConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            // Update UI with current config values
            document.getElementById('gridEnabledSwitch').checked = data.grid_enabled;
            document.getElementById('gridStatusLabel').textContent = data.grid_enabled ? 'Connected' : 'Disconnected';
            document.getElementById('electricityRateInput').value = data.electricity_rate;
            document.getElementById('gridMaxPowerInput').value = data.grid_max_power || 10000;
            
            document.getElementById('homeBatteryEnabledSwitch').checked = data.home_battery_enabled;
            document.getElementById('homeBatteryStatusLabel').textContent = data.home_battery_enabled ? 'Enabled' : 'Disabled';
            document.getElementById('homeBatteryCapacityInput').value = data.home_battery_capacity;
            document.getElementById('homeBatteryMaxOutputInput').value = data.home_battery_max_output || 5000;
            document.getElementById('homeBatteryMaxInputInput').value = data.home_battery_max_input || 3500;
            document.getElementById('homeBatteryLevelInput').value = data.home_battery_level;
            document.getElementById('homeBatteryLevelValue').textContent = `${data.home_battery_level}%`;
            
            // Set home battery mode
            const homeBatteryMode = data.home_battery_mode || 'idle';
            document.getElementById(`homeBattery${capitalizeFirstLetter(homeBatteryMode)}`).checked = true;
            
            document.getElementById('carBatteryEnabledSwitch').checked = data.car_battery_enabled;
            document.getElementById('carBatteryStatusLabel').textContent = data.car_battery_enabled ? 'Enabled' : 'Disabled';
            document.getElementById('carConnectedSwitch').checked = data.car_connected;
            document.getElementById('carConnectedSwitch').disabled = !data.car_battery_enabled;
            document.getElementById('carConnectedStatusLabel').textContent = data.car_connected ? 'Connected' : 'Disconnected';
            document.getElementById('carBatteryCapacityInput').value = data.car_battery_capacity;
            document.getElementById('carBatteryMaxOutputInput').value = data.car_battery_max_output || 7500;
            document.getElementById('carBatteryMaxInputInput').value = data.car_battery_max_input || 11000;
            document.getElementById('carBatteryLevelInput').value = data.car_battery_level;
            document.getElementById('carBatteryLevelValue').textContent = `${data.car_battery_level}%`;
            
            // Set car battery mode
            const carBatteryMode = data.car_battery_mode || 'idle';
            document.getElementById(`carBattery${capitalizeFirstLetter(carBatteryMode)}`).checked = true;
            
            
            // Disable controls for disabled components
            if (!data.home_battery_enabled) {
                const controls = ['homeBatteryCapacityInput', 'homeBatteryMaxOutputInput', 
                                  'homeBatteryMaxInputInput', 'homeBatteryLevelInput', 
                                  'simulateBatteryChargeBtn', 'simulateBatteryDischargeBtn'];
                
                controls.forEach(id => {
                    document.getElementById(id).disabled = true;
                });
                
                document.querySelectorAll('input[name="homeBatteryMode"]').forEach(radio => {
                    radio.disabled = true;
                });
            }
            
            if (!data.car_battery_enabled) {
                const controls = ['carConnectedSwitch', 'carBatteryCapacityInput', 'carBatteryMaxOutputInput', 
                                  'carBatteryMaxInputInput', 'carBatteryLevelInput', 'simulateCarTripBtn'];
                
                controls.forEach(id => {
                    document.getElementById(id).disabled = true;
                });
                
                document.querySelectorAll('input[name="carBatteryMode"]').forEach(radio => {
                    radio.disabled = true;
                });
            }
        })
        .catch(error => {
            console.error('Error loading config:', error);
            logSimulation('Error loading configuration');
        });
}

function updateConfig(config) {
    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            logSimulation('Error updating configuration');
        }
    })
    .catch(error => {
        console.error('Error updating config:', error);
        logSimulation('Error updating configuration');
    });
}

function logSimulation(message) {
    const log = document.getElementById('simulationLog');
    const timestamp = new Date().toLocaleTimeString();
    log.textContent = `[${timestamp}] ${message}\n${log.textContent}`;
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

// Helper functions for load simulations
function turnOnHighLoadDevices() {
    // Get all devices
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            // Turn on all high-power devices
            const promises = [];
            
            // Process real devices
            data.real_devices.forEach(device => {
                promises.push(
                    fetch('/api/devices/control', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            id: device.id,
                            action: 'power',
                            value: true
                        })
                    })
                );
            });
            
            // Process mock devices (focus on high-power ones)
            const highPowerTypes = ['air_conditioner', 'heater', 'oven', 'dryer', 'dishwasher'];
            
            data.mock_devices.forEach(device => {
                if (highPowerTypes.includes(device.type) || device.avg_power > 500) {
                    promises.push(
                        fetch('/api/devices/control', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                id: device.id,
                                action: 'power',
                                value: true
                            })
                        })
                    );
                }
            });
            
            Promise.all(promises)
                .then(() => {
                    logSimulation('High load scenario activated: major appliances turned on');
                })
                .catch(error => {
                    console.error('Error in high load simulation:', error);
                    logSimulation('Error in high load simulation');
                });
        })
        .catch(error => {
            console.error('Error loading devices:', error);
            logSimulation('Error loading devices for simulation');
        });
}

function turnOffMostDevices() {
    // Get all devices
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            // Turn off most devices except essentials
            const promises = [];
            const essentialTypes = ['refrigerator', 'security'];
            
            // Process all devices
            const allDevices = [
                ...data.real_devices,
                ...data.mock_devices
            ];
            
            allDevices.forEach(device => {
                if (!essentialTypes.includes(device.type)) {
                    promises.push(
                        fetch('/api/devices/control', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                id: device.id,
                                action: 'power',
                                value: false
                            })
                        })
                    );
                }
            });
            
            Promise.all(promises)
                .then(() => {
                    logSimulation('Low load scenario activated: most devices turned off');
                })
                .catch(error => {
                    console.error('Error in low load simulation:', error);
                    logSimulation('Error in low load simulation');
                });
        })
        .catch(error => {
            console.error('Error loading devices:', error);
            logSimulation('Error loading devices for simulation');
        });
}

function simulateRandomEvents() {
    // Choose a random event to simulate
    const events = [
        { name: 'Brief power flicker', action: simulatePowerFlicker },
        { name: 'Battery drain event', action: simulateBatteryDrain },
        { name: 'Device power spike', action: simulateDevicePowerSpike },
        { name: 'Car arrival with low battery', action: simulateCarArrival }
    ];
    
    const randomEvent = events[Math.floor(Math.random() * events.length)];
    logSimulation(`Random event selected: ${randomEvent.name}`);
    randomEvent.action();
}

function simulatePowerFlicker() {
    // Save current grid status
    const gridWasEnabled = document.getElementById('gridEnabledSwitch').checked;
    
    // Turn off grid briefly
    updateConfig({ 'grid_enabled': false });
    document.getElementById('gridEnabledSwitch').checked = false;
    document.getElementById('gridStatusLabel').textContent = 'Disconnected';
    logSimulation('Grid power flicker (outage) started');
    
    // Restore grid after 3 seconds
    setTimeout(() => {
        updateConfig({ 'grid_enabled': gridWasEnabled });
        document.getElementById('gridEnabledSwitch').checked = gridWasEnabled;
        document.getElementById('gridStatusLabel').textContent = gridWasEnabled ? 'Connected' : 'Disconnected';
        logSimulation('Grid power restored after flicker');
    }, 3000);
}

function simulateBatteryDrain() {
    // Get current battery level
    const currentLevel = parseInt(document.getElementById('homeBatteryLevelInput').value);
    
    // Drain battery by 15-30%
    const drainAmount = Math.floor(Math.random() * 15) + 15;
    const newLevel = Math.max(5, currentLevel - drainAmount);
    
    // Update battery level
    updateConfig({ 'home_battery_level': newLevel });
    document.getElementById('homeBatteryLevelInput').value = newLevel;
    document.getElementById('homeBatteryLevelValue').textContent = `${newLevel}%`;
    
    logSimulation(`Simulated rapid battery drain: level decreased from ${currentLevel}% to ${newLevel}%`);
}

function simulateDevicePowerSpike() {
    // This is a simulated event - we would need to implement temporary power spikes
    // in the device manager for a real implementation
    logSimulation('Simulated device power spike: some device momentarily drew high power');
    
    // For visual feedback, we'll flash the battery levels briefly
    const homeBatteryLevel = document.getElementById('homeBatteryLevel');
    const originalClass = homeBatteryLevel ? homeBatteryLevel.className : '';
    
    if (homeBatteryLevel) {
        homeBatteryLevel.className = 'progress-bar bg-danger';
        
        setTimeout(() => {
            homeBatteryLevel.className = originalClass;
        }, 2000);
    }
}

function simulateCarArrival() {
    // Connect car with a low battery
    const lowBatteryLevel = Math.floor(Math.random() * 15) + 20; // 20-35%
    
    updateConfig({
        'car_connected': true,
        'car_battery_enabled': true,
        'car_battery_level': lowBatteryLevel
    });
    
    // Update UI
    document.getElementById('carConnectedSwitch').checked = true;
    document.getElementById('carConnectedStatusLabel').textContent = 'Connected';
    document.getElementById('carBatteryEnabledSwitch').checked = true;
    document.getElementById('carBatteryStatusLabel').textContent = 'Enabled';
    document.getElementById('carBatteryLevelInput').value = lowBatteryLevel;
    document.getElementById('carBatteryLevelValue').textContent = `${lowBatteryLevel}%`;
    
    logSimulation(`Simulated car arrival: EV connected with ${lowBatteryLevel}% battery`);
}