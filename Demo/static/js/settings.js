// Settings JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Load devices
    loadDevices();
    
    // Load config
    loadConfig();
    
    // Set up event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // Form submissions
    document.getElementById('addRealDeviceForm').addEventListener('submit', function(event) {
        event.preventDefault();
        addRealDevice();
    });
    
    document.getElementById('addMockDeviceForm').addEventListener('submit', function(event) {
        event.preventDefault();
        addMockDevice();
    });
    
    document.getElementById('tapoAccountForm').addEventListener('submit', function(event) {
        event.preventDefault();
        updateTapoAccount();
    });
    
    // Power source settings forms
    document.getElementById('gridSettingsForm').addEventListener('submit', function(event) {
        event.preventDefault();
        updatePowerSourceSettings('grid');
    });
    
    document.getElementById('homeBatterySettingsForm').addEventListener('submit', function(event) {
        event.preventDefault();
        updatePowerSourceSettings('home_battery');
    });
    
    document.getElementById('carBatterySettingsForm').addEventListener('submit', function(event) {
        event.preventDefault();
        updatePowerSourceSettings('car_battery');
    });
}

function loadConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            // Update power source settings form fields
            document.getElementById('gridEnabledSwitch').checked = data.grid_enabled;
            document.getElementById('electricityRateInput').value = data.electricity_rate;
            
            document.getElementById('homeBatteryEnabledSwitch').checked = data.home_battery_enabled;
            document.getElementById('homeBatteryCapacityInput').value = data.home_battery_capacity;
            
            document.getElementById('carBatteryEnabledSwitch').checked = data.car_battery_enabled;
            document.getElementById('carBatteryCapacityInput').value = data.car_battery_capacity;
        })
        .catch(error => {
            console.error('Error loading config:', error);
            alert('Error loading configuration. Please check the console for details.');
        });
}

function loadDevices() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            updateRealDevicesList(data.real_devices);
            updateMockDevicesList(data.mock_devices);
        })
        .catch(error => {
            console.error('Error loading devices:', error);
            alert('Error loading devices. Please check the console for details.');
        });
}

function updateRealDevicesList(devices) {
    const realDevicesList = document.getElementById('realDevicesList');
    const noRealDevices = document.getElementById('noRealDevices');
    
    realDevicesList.innerHTML = '';
    
    if (devices.length === 0) {
        noRealDevices.style.display = 'block';
        return;
    }
    
    noRealDevices.style.display = 'none';
    
    devices.forEach(device => {
        const deviceRow = document.createElement('tr');
        
        deviceRow.innerHTML = `
            <td>${device.name}</td>
            <td>${device.type}</td>
            <td>${device.ip}</td>
            <td>
                <span class="badge ${device.is_on ? 'bg-success' : 'bg-secondary'}">
                    ${device.is_on ? 'ON' : 'OFF'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-danger remove-device" data-id="${device.id}">
                    <i class="bi bi-trash"></i> Remove
                </button>
            </td>
        `;
        
        realDevicesList.appendChild(deviceRow);
    });
    
    // Add event listeners to remove buttons
    document.querySelectorAll('.remove-device').forEach(button => {
        button.addEventListener('click', function() {
            const deviceId = this.getAttribute('data-id');
            removeDevice(deviceId);
        });
    });
}

function updateMockDevicesList(devices) {
    const mockDevicesList = document.getElementById('mockDevicesList');
    const noMockDevices = document.getElementById('noMockDevices');
    
    mockDevicesList.innerHTML = '';
    
    if (devices.length === 0) {
        noMockDevices.style.display = 'block';
        return;
    }
    
    noMockDevices.style.display = 'none';
    
    devices.forEach(device => {
        const deviceRow = document.createElement('tr');
        
        deviceRow.innerHTML = `
            <td>${device.name}</td>
            <td>${device.type}</td>
            <td>${device.avg_power} W</td>
            <td>
                <span class="badge ${device.is_on ? 'bg-success' : 'bg-secondary'}">
                    ${device.is_on ? 'ON' : 'OFF'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-danger remove-device" data-id="${device.id}">
                    <i class="bi bi-trash"></i> Remove
                </button>
            </td>
        `;
        
        mockDevicesList.appendChild(deviceRow);
    });
    
    // Add event listeners to remove buttons
    document.querySelectorAll('.remove-device').forEach(button => {
        button.addEventListener('click', function() {
            const deviceId = this.getAttribute('data-id');
            removeDevice(deviceId);
        });
    });
}

function addRealDevice() {
    const name = document.getElementById('realDeviceName').value;
    const type = document.getElementById('realDeviceType').value;
    const ip = document.getElementById('realDeviceIP').value;
    
    fetch('/api/devices/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: 'real',
            id: generateId(),
            name: name,
            device_type: type,
            ip: ip
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear form
            document.getElementById('realDeviceName').value = '';
            document.getElementById('realDeviceType').selectedIndex = 0;
            document.getElementById('realDeviceIP').value = '';
            
            // Reload devices
            loadDevices();
            
            // Show success
            alert('Real device added successfully!');
        } else {
            alert('Error adding device: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error adding device:', error);
        alert('Error adding device. Please check the console for details.');
    });
}

function addMockDevice() {
    const name = document.getElementById('mockDeviceName').value;
    const type = document.getElementById('mockDeviceType').value;
    const power = document.getElementById('mockDevicePower').value;
    const isDimmable = document.getElementById('mockDeviceDimmable').checked;
    
    fetch('/api/devices/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: 'mock',
            id: generateId(),
            name: name,
            device_type: type,
            avg_power: power,
            is_dimmable: isDimmable ? 'true' : 'false'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear form
            document.getElementById('mockDeviceName').value = '';
            document.getElementById('mockDeviceType').selectedIndex = 0;
            document.getElementById('mockDevicePower').value = '100';
            document.getElementById('mockDeviceDimmable').checked = false;
            
            // Reload devices
            loadDevices();
            
            // Show success
            alert('Mock device added successfully!');
        } else {
            alert('Error adding device: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error adding device:', error);
        alert('Error adding device. Please check the console for details.');
    });
}

function removeDevice(deviceId) {
    if (confirm('Are you sure you want to remove this device?')) {
        fetch('/api/devices/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: deviceId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload devices
                loadDevices();
            } else {
                alert('Error removing device: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error removing device:', error);
            alert('Error removing device. Please check the console for details.');
        });
    }
}

function updateTapoAccount() {
    const username = document.getElementById('tapoUsername').value;
    const password = document.getElementById('tapoPassword').value;
    
    // Only include password if it's not empty
    const data = { username: username };
    if (password) {
        data.password = password;
    }
    
    fetch('/api/setup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear password field
            document.getElementById('tapoPassword').value = '';
            
            // Show success
            alert('Tapo account settings updated successfully!');
        } else {
            alert('Error updating Tapo account: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error updating Tapo account:', error);
        alert('Error updating Tapo account. Please check the console for details.');
    });
}

function updatePowerSourceSettings(sourceType) {
    const configData = {};
    
    if (sourceType === 'grid') {
        configData.grid_enabled = document.getElementById('gridEnabledSwitch').checked;
        configData.electricity_rate = parseFloat(document.getElementById('electricityRateInput').value);
    } else if (sourceType === 'home_battery') {
        configData.home_battery_enabled = document.getElementById('homeBatteryEnabledSwitch').checked;
        configData.home_battery_capacity = parseFloat(document.getElementById('homeBatteryCapacityInput').value);
    } else if (sourceType === 'car_battery') {
        configData.car_battery_enabled = document.getElementById('carBatteryEnabledSwitch').checked;
        configData.car_battery_capacity = parseFloat(document.getElementById('carBatteryCapacityInput').value);
    }
    
    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`${sourceType.replace('_', ' ').charAt(0).toUpperCase() + sourceType.replace('_', ' ').slice(1)} settings updated successfully!`);
        } else {
            alert('Error updating settings: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error updating settings:', error);
        alert('Error updating settings. Please check the console for details.');
    });
}

// Helper function to generate a random ID
function generateId() {
    return 'device-' + Math.random().toString(36).substring(2, 10);
}