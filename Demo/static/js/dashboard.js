// Dashboard JavaScript

// Charts
let powerGaugeChart;
let powerSourcesChart;
let historicalChart;

// Global variables for power distribution
let powerPriority = {
    first: 'grid',
    second: 'home_battery',
    third: 'car_battery'
};

// Battery states
const BATTERY_STATE = {
    IDLE: 'idle',
    CHARGING: 'charging',
    IN_USE: 'in_use'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initial data load
    loadEnergyStatus();
    loadDevices();
    loadHistoricalData('day');
    
    // Set up refresh interval
    setInterval(loadEnergyStatus, 10000); // Refresh every 10 seconds
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize charts
    initializeCharts();
});

function setupEventListeners() {
    // Priority selection dropdowns
    const prioritySelects = document.querySelectorAll('.priority-select');
    prioritySelects.forEach(select => {
        select.addEventListener('change', function() {
            updatePrioritySelections();
        });
    });

    // Home battery mode controls
    document.getElementById('homeBatteryChargeBtn').addEventListener('click', function() {
        controlBatteryMode('home', BATTERY_STATE.CHARGING);
    });
    
    document.getElementById('homeBatteryUseBtn').addEventListener('click', function() {
        controlBatteryMode('home', BATTERY_STATE.IN_USE);
    });
    
    document.getElementById('homeBatteryIdleBtn').addEventListener('click', function() {
        controlBatteryMode('home', BATTERY_STATE.IDLE);
    });
    
    // Car battery mode controls
    document.getElementById('carBatteryChargeBtn').addEventListener('click', function() {
        controlBatteryMode('car', BATTERY_STATE.CHARGING);
    });
    
    document.getElementById('carBatteryUseBtn').addEventListener('click', function() {
        controlBatteryMode('car', BATTERY_STATE.IN_USE);
    });
    
    document.getElementById('carBatteryIdleBtn').addEventListener('click', function() {
        controlBatteryMode('car', BATTERY_STATE.IDLE);
    });
    
    // Car connection buttons
    document.getElementById('connectCarBtn').addEventListener('click', function() {
        controlBattery('car', 'connect');
    });
    
    document.getElementById('disconnectCarBtn').addEventListener('click', function() {
        controlBattery('car', 'disconnect');
    });
    
    // Historical chart period buttons
    const periodButtons = document.querySelectorAll('[data-period]');
    periodButtons.forEach(button => {
        button.addEventListener('click', function() {
            const period = this.getAttribute('data-period');
            loadHistoricalData(period);
            
            // Update active button
            periodButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function updatePrioritySelections() {
    const firstPriority = document.getElementById('firstPriority').value;
    const secondPriority = document.getElementById('secondPriority').value;
    const thirdPriority = document.getElementById('thirdPriority').value;
    
    // Validate that all priorities are different
    const allSources = ['grid', 'home_battery', 'car_battery'];
    const selectedSources = new Set([firstPriority, secondPriority, thirdPriority]);
    
    // If we don't have all 3 unique values, something's duplicated
    if (selectedSources.size !== 3) {
        // Find which source is missing
        const missingSource = allSources.find(source => !selectedSources.has(source));
        
        // Find which one is duplicated (the one that's not the currently changed dropdown)
        const activeElement = document.activeElement;
        
        if (activeElement && activeElement.classList.contains('priority-select')) {
            const activeId = activeElement.id;
            const otherSelects = Array.from(document.querySelectorAll('.priority-select'))
                .filter(select => select.id !== activeId);
            
            // Find the duplicate value
            const duplicateValue = firstPriority === secondPriority ? firstPriority : 
                                  (firstPriority === thirdPriority ? firstPriority : secondPriority);
            
            // Find which other dropdown has the duplicate and change it
            for (const select of otherSelects) {
                if (select.value === duplicateValue) {
                    select.value = missingSource;
                    break;
                }
            }
        }
    }
    
    // Update our priority object with the current values
    powerPriority.first = document.getElementById('firstPriority').value;
    powerPriority.second = document.getElementById('secondPriority').value;
    powerPriority.third = document.getElementById('thirdPriority').value;
    
    // Send updated priority to backend
    updatePowerPriority();
}

function updatePowerPriority() {
    fetch('/api/power/priority', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            priorities: [
                powerPriority.first,
                powerPriority.second,
                powerPriority.third
            ]
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Refresh energy status to reflect the new distribution
            loadEnergyStatus();
        }
    })
    .catch(error => {
        console.error('Error updating power priorities:', error);
    });
}

function updateCarConnectionUI(isConnected) {
    document.getElementById('connectCarBtn').disabled = isConnected;
    document.getElementById('disconnectCarBtn').disabled = !isConnected;
    
    const batteryButtons = ['carBatteryChargeBtn', 'carBatteryUseBtn', 'carBatteryIdleBtn'];
    batteryButtons.forEach(id => {
        document.getElementById(id).disabled = !isConnected;
    });
}

function initializeCharts() {
    // Power gauge chart - simplified for better responsiveness
    const powerGaugeCtx = document.getElementById('powerGauge').getContext('2d');
    powerGaugeChart = new Chart(powerGaugeCtx, {
        type: 'doughnut',
        data: {
            labels: ['Current Power', ''],
            datasets: [{
                data: [0, 100],
                backgroundColor: ['#0d6efd', '#e9ecef'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '75%',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        }
    });
    
    // Power sources chart - horizontal bar for better space utilization
    const powerSourcesCtx = document.getElementById('powerSourcesChart').getContext('2d');
    powerSourcesChart = new Chart(powerSourcesCtx, {
        type: 'bar',
        data: {
            labels: ['Energy Sources'],
            datasets: [
                {
                    label: 'Grid',
                    backgroundColor: '#6c757d',
                    data: [0]
                },
                {
                    label: 'Home Battery',
                    backgroundColor: '#198754',
                    data: [0]
                },
                {
                    label: 'Car Battery',
                    backgroundColor: '#0dcaf0',
                    data: [0]
                }
            ]
        },
        options: {
            indexAxis: 'y',  // Make horizontal bar chart
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Watts'
                    }
                },
                y: {
                    stacked: true
                }
            }
        }
    });
    
    // Historical chart - with improved responsiveness
    const historicalCtx = document.getElementById('historicalChart').getContext('2d');
    historicalChart = new Chart(historicalCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Total Usage',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderColor: '#0d6efd',
                    borderWidth: 2,
                    fill: true,
                    data: []
                },
                {
                    label: 'Grid',
                    borderColor: '#6c757d',
                    borderWidth: 2,
                    fill: false,
                    data: []
                },
                {
                    label: 'Home Battery',
                    borderColor: '#198754',
                    borderWidth: 2,
                    fill: false,
                    data: []
                },
                {
                    label: 'Car Battery',
                    borderColor: '#0dcaf0',
                    borderWidth: 2,
                    fill: false,
                    data: []
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Watts'
                    }
                },
                x: {
                    ticks: {
                        maxTicksLimit: 8,  // Limit the number of x-axis labels for better readability
                        maxRotation: 0
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end'
                }
            }
        }
    });
}

function loadEnergyStatus() {
    fetch('/api/energy/status')
        .then(response => response.json())
        .then(data => {
            console.log("Energy status data:", data); // Debug
            updateEnergyDisplay(data);
            updateCharts(data);
            updatePowerPriorityUI(data);
        })
        .catch(error => {
            console.error('Error loading energy status:', error);
        });
}

function updatePowerPriorityUI(data) {
    // Disable power sources in dropdowns that aren't available
    const firstPriority = document.getElementById('firstPriority');
    const secondPriority = document.getElementById('secondPriority');
    const thirdPriority = document.getElementById('thirdPriority');
    
    // Check grid availability
    const gridOption = Array.from(firstPriority.options).find(option => option.value === 'grid');
    if (gridOption) {
        gridOption.disabled = !data.grid_enabled;
    }
    
    // Check home battery availability
    const homeBatteryOption = Array.from(firstPriority.options).find(option => option.value === 'home_battery');
    if (homeBatteryOption) {
        homeBatteryOption.disabled = !data.home_battery_enabled || data.home_battery_mode !== 'in_use';
    }
    
    // Check car battery availability
    const carBatteryOption = Array.from(firstPriority.options).find(option => option.value === 'car_battery');
    if (carBatteryOption) {
        carBatteryOption.disabled = !data.car_battery_enabled || !data.car_connected || data.car_battery_mode !== 'in_use';
    }
    
    // Apply same disabling to other dropdowns
    for (const option of Array.from(secondPriority.options)) {
        if (option.value === 'grid') {
            option.disabled = !data.grid_enabled;
        } else if (option.value === 'home_battery') {
            option.disabled = !data.home_battery_enabled || data.home_battery_mode !== 'in_use';
        } else if (option.value === 'car_battery') {
            option.disabled = !data.car_battery_enabled || !data.car_connected || data.car_battery_mode !== 'in_use';
        }
    }
    
    for (const option of Array.from(thirdPriority.options)) {
        if (option.value === 'grid') {
            option.disabled = !data.grid_enabled;
        } else if (option.value === 'home_battery') {
            option.disabled = !data.home_battery_enabled || data.home_battery_mode !== 'in_use';
        } else if (option.value === 'car_battery') {
            option.disabled = !data.car_battery_enabled || !data.car_connected || data.car_battery_mode !== 'in_use';
        }
    }
}

function loadDevices() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            updateDevicesList(data);
        })
        .catch(error => {
            console.error('Error loading devices:', error);
        });
}

function loadHistoricalData(period) {
    fetch(`/api/energy/history?period=${period}`)
        .then(response => response.json())
        .then(data => {
            updateHistoricalChart(data);
        })
        .catch(error => {
            console.error('Error loading historical data:', error);
        });
}

function updateEnergyDisplay(data) {
    // Update current power display
    document.getElementById('currentPower').textContent = data.total_power_usage.toFixed(1);
    
    // Update grid info
    document.getElementById('gridPower').textContent = `${data.grid_power.toFixed(1)} W`;
    document.getElementById('electricityRate').textContent = `$${data.electricity_rate.toFixed(2)}/kWh`;
    document.getElementById('dailyCost').textContent = `$${data.estimated_daily_cost.toFixed(2)}/day`;
    document.getElementById('gridCurrentUsage').textContent = `${data.grid_power.toFixed(1)} W`;
    document.getElementById('gridAvailablePower').textContent = `${data.grid_max_power.toFixed(1)} W`;
    
    // Update grid status and apply disabled styling if needed
    const gridCard = document.getElementById('gridCard');
    const gridStatus = document.getElementById('gridStatus');
    
    if (data.grid_enabled) {
        gridStatus.textContent = 'Connected';
        gridStatus.className = 'badge bg-success';
        gridCard.classList.remove('text-muted', 'opacity-50');
    } else {
        gridStatus.textContent = 'Disconnected';
        gridStatus.className = 'badge bg-secondary';
        gridCard.classList.add('text-muted', 'opacity-50');
    }
    
    // Update home battery info
    document.getElementById('homeBatteryPower').textContent = `${data.home_battery_power.toFixed(1)} W`;
    document.getElementById('homeBatteryCapacity').textContent = `${data.home_battery_capacity.toFixed(1)} kWh`;
    document.getElementById('homeBatteryEnergyLeft').textContent = `${((data.home_battery_level / 100) * data.home_battery_capacity).toFixed(1)} kWh`;
    document.getElementById('homeBatteryCurrentUsage').textContent = `${data.home_battery_power.toFixed(1)} W`;
    document.getElementById('homeBatteryMaxOutput').textContent = `${data.home_battery_max_output.toFixed(1)} W`;
    document.getElementById('homeBatteryMaxInput').textContent = `${data.home_battery_max_input.toFixed(1)} W`;
    
    // Update home battery status and level
    const homeBatteryCard = document.getElementById('homeBatteryCard');
    const homeBatteryStatus = document.getElementById('homeBatteryStatus');
    const homeBatteryLevel = document.getElementById('homeBatteryLevel');
    const homeBatteryButtons = {
        charge: document.getElementById('homeBatteryChargeBtn'),
        use: document.getElementById('homeBatteryUseBtn'),
        idle: document.getElementById('homeBatteryIdleBtn')
    };
    
    // Update mode
    document.getElementById('homeBatteryMode').textContent = data.home_battery_mode ? data.home_battery_mode.charAt(0).toUpperCase() + data.home_battery_mode.slice(1) : 'Idle';
    
    // Reset button styles
    Object.values(homeBatteryButtons).forEach(btn => btn.classList.remove('btn-active-state'));
    
    // Set active button
    if (data.home_battery_mode === BATTERY_STATE.CHARGING) {
        homeBatteryButtons.charge.classList.add('btn-active-state');
    } else if (data.home_battery_mode === BATTERY_STATE.IN_USE) {
        homeBatteryButtons.use.classList.add('btn-active-state');
    } else {
        homeBatteryButtons.idle.classList.add('btn-active-state');
    }
    
    if (data.home_battery_enabled) {
        homeBatteryStatus.textContent = 'Enabled';
        homeBatteryStatus.className = 'badge bg-success';
        homeBatteryCard.classList.remove('text-muted', 'opacity-50');
        
        // Update battery level
        homeBatteryLevel.style.width = `${data.home_battery_level}%`;
        homeBatteryLevel.textContent = `${data.home_battery_level.toFixed(0)}%`;
        
        // Enable buttons
        Object.values(homeBatteryButtons).forEach(btn => btn.disabled = false);
        
        // Update battery colors based on level
        if (data.home_battery_level < 20) {
            homeBatteryLevel.classList.remove('bg-success', 'bg-warning');
            homeBatteryLevel.classList.add('bg-danger');
        } else if (data.home_battery_level < 50) {
            homeBatteryLevel.classList.remove('bg-success', 'bg-danger');
            homeBatteryLevel.classList.add('bg-warning');
        } else {
            homeBatteryLevel.classList.remove('bg-warning', 'bg-danger');
            homeBatteryLevel.classList.add('bg-success');
        }
    } else {
        homeBatteryStatus.textContent = 'Disabled';
        homeBatteryStatus.className = 'badge bg-secondary';
        homeBatteryCard.classList.add('text-muted', 'opacity-50');
        
        // Set battery level to 0
        homeBatteryLevel.style.width = '0%';
        homeBatteryLevel.textContent = '0%';
        homeBatteryLevel.classList.remove('bg-success', 'bg-warning', 'bg-danger');
        homeBatteryLevel.classList.add('bg-secondary');
        
        // Disable buttons
        Object.values(homeBatteryButtons).forEach(btn => btn.disabled = true);
    }
    
    // Update car battery info
    document.getElementById('carBatteryPower').textContent = `${data.car_battery_power.toFixed(1)} W`;
    document.getElementById('carBatteryCapacityValue').textContent = `${data.car_battery_capacity.toFixed(1)} kWh`;
    document.getElementById('carBatteryEnergyLeft').textContent = `${((data.car_battery_level / 100) * data.car_battery_capacity).toFixed(1)} kWh`;
    document.getElementById('carBatteryCurrentUsage').textContent = `${data.car_battery_power.toFixed(1)} W`;
    document.getElementById('carBatteryMaxOutput').textContent = `${data.car_battery_max_output.toFixed(1)} W`;
    document.getElementById('carBatteryMaxInput').textContent = `${data.car_battery_max_input.toFixed(1)} W`;
    
    // Update car battery status and level
    const carBatteryCard = document.getElementById('carBatteryCard');
    const carBatteryStatus = document.getElementById('carBatteryStatus');
    const carBatteryLevel = document.getElementById('carBatteryLevel');
    const carButtons = {
        connect: document.getElementById('connectCarBtn'),
        disconnect: document.getElementById('disconnectCarBtn'),
        charge: document.getElementById('carBatteryChargeBtn'),
        use: document.getElementById('carBatteryUseBtn'),
        idle: document.getElementById('carBatteryIdleBtn')
    };
    
    // Update mode
    document.getElementById('carBatteryMode').textContent = data.car_battery_mode ? data.car_battery_mode.charAt(0).toUpperCase() + data.car_battery_mode.slice(1) : 'Idle';
    
    // Reset button styles
    [carButtons.charge, carButtons.use, carButtons.idle].forEach(btn => btn.classList.remove('btn-active-state'));
    
    // Set active button
    if (data.car_battery_mode === BATTERY_STATE.CHARGING) {
        carButtons.charge.classList.add('btn-active-state');
    } else if (data.car_battery_mode === BATTERY_STATE.IN_USE) {
        carButtons.use.classList.add('btn-active-state');
    } else {
        carButtons.idle.classList.add('btn-active-state');
    }
    
    if (data.car_battery_enabled) {
        carBatteryStatus.textContent = 'Enabled';
        carBatteryStatus.className = 'badge bg-success';
        carBatteryCard.classList.remove('text-muted', 'opacity-50');
        
        // Update battery level
        carBatteryLevel.style.width = `${data.car_battery_level}%`;
        carBatteryLevel.textContent = `${data.car_battery_level.toFixed(0)}%`;
        
        // Update car connection status
        document.getElementById('carStatus').textContent = data.car_connected ? 'Connected' : 'Disconnected';
        
        // Update car connection buttons
        carButtons.connect.disabled = data.car_connected;
        carButtons.disconnect.disabled = !data.car_connected;
        
        // Mode buttons are only enabled if connected
        carButtons.charge.disabled = !data.car_connected;
        carButtons.use.disabled = !data.car_connected;
        carButtons.idle.disabled = !data.car_connected;
        
        // Update battery colors based on level
        if (data.car_battery_level < 20) {
            carBatteryLevel.classList.remove('bg-info', 'bg-warning');
            carBatteryLevel.classList.add('bg-danger');
        } else if (data.car_battery_level < 50) {
            carBatteryLevel.classList.remove('bg-info', 'bg-danger');
            carBatteryLevel.classList.add('bg-warning');
        } else {
            carBatteryLevel.classList.remove('bg-warning', 'bg-danger');
            carBatteryLevel.classList.add('bg-info');
        }
    } else {
        carBatteryStatus.textContent = 'Disabled';
        carBatteryStatus.className = 'badge bg-secondary';
        carBatteryCard.classList.add('text-muted', 'opacity-50');
        
        // Set battery level to 0
        carBatteryLevel.style.width = '0%';
        carBatteryLevel.textContent = '0%';
        carBatteryLevel.classList.remove('bg-info', 'bg-warning', 'bg-danger');
        carBatteryLevel.classList.add('bg-secondary');
        
        // Update car connection status
        document.getElementById('carStatus').textContent = 'Disconnected';
        
        // Disable all buttons
        carButtons.connect.disabled = true;
        carButtons.disconnect.disabled = true;
        carButtons.charge.disabled = true;
        carButtons.use.disabled = true;
        carButtons.idle.disabled = true;
    }
}

function updateCharts(data) {
    console.log("Updating charts with data:", data);
    
    // Ensure we have valid values for display
    let totalPower = Math.max(0, data.total_power_usage || 0);
    let gridPower = Math.max(0, data.grid_power || 0);
    let homeBatteryPower = Math.max(0, data.home_battery_power || 0);
    let carBatteryPower = Math.max(0, data.car_battery_power || 0);
    
    // Update power gauge chart
    // Scale the power to a max of 5000W for the gauge
    let scaledPower = totalPower;
    let maxPower = 5000;
    
    if (scaledPower > maxPower) {
        scaledPower = maxPower;
    }
    
    let percentage = totalPower > 0 ? (scaledPower / maxPower) * 100 : 0;
    console.log("Gauge percentage:", percentage);
    
    powerGaugeChart.data.datasets[0].data = [percentage, 100 - percentage];
    powerGaugeChart.update();
    
    // Update power sources chart with minimal values to ensure visibility
    powerSourcesChart.data.datasets[0].data = [gridPower];
    powerSourcesChart.data.datasets[1].data = [homeBatteryPower];
    powerSourcesChart.data.datasets[2].data = [carBatteryPower];
    powerSourcesChart.update();
    
    // Update shortfall indication if applicable
    // Use the already declared totalPower variable (no redeclaration)
    const suppliedPower = gridPower + homeBatteryPower + carBatteryPower;
    
    if (suppliedPower < totalPower && document.getElementById('powerShortfall')) {
        const shortfall = totalPower - suppliedPower;
        document.getElementById('powerShortfall').style.display = 'block';
        document.getElementById('shortfallValue').textContent = shortfall.toFixed(1);
        document.getElementById('shortfallPercentage').textContent = 
            Math.round((shortfall / totalPower) * 100);
    } else if (document.getElementById('powerShortfall')) {
        document.getElementById('powerShortfall').style.display = 'none';
    }
}

function updateHistoricalChart(data) {
    // Format timestamps to readable labels
    const labels = data.timestamps.map(timestamp => {
        const date = new Date(timestamp * 1000);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
    
    // Update chart data
    historicalChart.data.labels = labels;
    historicalChart.data.datasets[0].data = data.total_usage;
    historicalChart.data.datasets[1].data = data.grid_power;
    historicalChart.data.datasets[2].data = data.home_battery_power;
    historicalChart.data.datasets[3].data = data.car_battery_power;
    
    historicalChart.update();
}

function updateDevicesList(data) {
    const devicesList = document.getElementById('devicesList');
    devicesList.innerHTML = '';
    
    // Combine both real and mock devices
    const allDevices = [
        ...data.real_devices.map(device => ({ ...device, type: 'real' })),
        ...data.mock_devices.map(device => ({ ...device, type: 'mock' }))
    ];
    
    if (allDevices.length === 0) {
        devicesList.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">No devices configured. Add devices in the settings.</td>
            </tr>
        `;
        return;
    }
    
    allDevices.forEach(device => {
        const deviceRow = document.createElement('tr');
        
        // Determine power display
        let powerDisplay = '';
        if (device.is_on) {
            if (device.type === 'mock') {
                let power = device.avg_power;
                if (device.is_dimmable && device.dimming_level < 100) {
                    power = Math.round(power * (device.dimming_level / 100));
                }
                powerDisplay = `${power} W`;
            } else {
                powerDisplay = `${device.power || '?'} W`;
            }
        } else {
            powerDisplay = '0 W';
        }
        
        // Create dimming control if applicable
        let dimmingControl = '';
        if (device.is_dimmable) {
            dimmingControl = `
                <div class="mt-2">
                    <label class="form-label small mb-0">Brightness: ${device.dimming_level || 100}%</label>
                    <input type="range" class="form-range device-dimming" 
                        data-id="${device.id}" 
                        value="${device.dimming_level || 100}" 
                        min="10" max="100" step="10"
                        ${!device.is_on ? 'disabled' : ''}>
                </div>
            `;
        }
        
        deviceRow.innerHTML = `
            <td>${device.name}</td>
            <td>${device.type}</td>
            <td>${powerDisplay}</td>
            <td>
                <span class="badge ${device.is_on ? 'bg-success' : 'bg-secondary'}">
                    ${device.is_on ? 'ON' : 'OFF'}
                </span>
            </td>
            <td>
                <div class="form-check form-switch">
                    <input class="form-check-input device-toggle" type="checkbox" 
                        data-id="${device.id}" ${device.is_on ? 'checked' : ''}>
                </div>
                ${dimmingControl}
            </td>
        `;
        
        devicesList.appendChild(deviceRow);
    });
    
    // Add event listeners for device controls
    document.querySelectorAll('.device-toggle').forEach(toggle => {
        toggle.addEventListener('change', function() {
            const deviceId = this.getAttribute('data-id');
            const isOn = this.checked;
            controlDevice(deviceId, 'power', isOn);
            
            // Enable/disable dimming controls immediately in UI
            const dimmingControl = this.closest('tr').querySelector('.device-dimming');
            if (dimmingControl) {
                dimmingControl.disabled = !isOn;
            }
            
            // Update status badge immediately
            const statusBadge = this.closest('tr').querySelector('.badge');
            if (statusBadge) {
                statusBadge.className = isOn ? 'badge bg-success' : 'badge bg-secondary';
                statusBadge.textContent = isOn ? 'ON' : 'OFF';
            }
        });
    });
    
    document.querySelectorAll('.device-dimming').forEach(slider => {
        slider.addEventListener('change', function() {
            const deviceId = this.getAttribute('data-id');
            const dimmingValue = this.value;
            
            // If slider is moved, also ensure the device is turned on
            const toggle = this.closest('tr').querySelector('.device-toggle');
            if (toggle && !toggle.checked) {
                toggle.checked = true;
                
                // Update status badge
                const statusBadge = this.closest('tr').querySelector('.badge');
                if (statusBadge) {
                    statusBadge.className = 'badge bg-success';
                    statusBadge.textContent = 'ON';
                }
                
                // First turn on the device, then set dimming
                controlDevice(deviceId, 'power', true).then(() => {
                    controlDevice(deviceId, 'dimming', dimmingValue);
                });
            } else {
                controlDevice(deviceId, 'dimming', dimmingValue);
            }
            
            // Update label immediately
            const label = this.previousElementSibling;
            label.textContent = `Brightness: ${this.value}%`;
        });
    });
}

// Update the controlDevice function to return a promise
function controlDevice(deviceId, action, value) {
    return fetch('/api/devices/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id: deviceId,
            action: action,
            value: value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadEnergyStatus();
            return data;  // Return data for promise chaining
        } else if (data.error) {
            alert(`Error: ${data.error}`);
            throw new Error(data.error);  // Throw error for promise catch
        }
    })
    .catch(error => {
        console.error('Error controlling device:', error);
        throw error;  // Re-throw for promise catch
    });
}

function controlBatteryMode(type, mode) {
    fetch('/api/battery/mode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: type,
            mode: mode
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadEnergyStatus();
        }
    })
    .catch(error => {
        console.error(`Error setting ${type} battery mode:`, error);
    });
}

function controlBattery(type, action) {
    fetch('/api/battery/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: type,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadEnergyStatus();
        }
    })
    .catch(error => {
        console.error('Error controlling battery:', error);
    });
}

function controlDevice(deviceId, action, value) {
    fetch('/api/devices/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id: deviceId,
            action: action,
            value: value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadEnergyStatus();
        } else if (data.error) {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error controlling device:', error);
    });
}