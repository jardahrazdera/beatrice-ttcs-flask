/**
 * Dashboard JavaScript - Real-time monitoring and updates
 */

// WebSocket connection
let socket;

// Chart.js instance
let temperatureChart;

// Temperature history data
const temperatureHistory = {
    labels: [],
    tank1: [],
    tank2: [],
    tank3: [],
    average: []
};

const MAX_HISTORY_POINTS = 60; // Keep last 60 data points

// Connection status tracking
let lastUpdateTime = null;
let staleDataCheckInterval = null;
const STALE_DATA_THRESHOLD = 30000; // 30 seconds in milliseconds

/**
 * Update connection status indicator
 */
function updateConnectionStatus(status, text) {
    const pulse = document.getElementById('connection-pulse');
    const statusText = document.getElementById('connection-status');

    if (pulse) {
        pulse.className = 'connection-pulse ' + status;
    }

    if (statusText) {
        statusText.textContent = text;
    }
}

/**
 * Update last update timestamp
 */
function updateLastUpdateTime() {
    const lastUpdateEl = document.getElementById('last-update');
    if (!lastUpdateEl || !lastUpdateTime) return;

    const now = new Date();
    const diff = Math.floor((now - lastUpdateTime) / 1000); // seconds

    let text;
    if (diff < 10) {
        text = 'Právě teď';
    } else if (diff < 60) {
        text = `Před ${diff} sekundami`;
    } else {
        const minutes = Math.floor(diff / 60);
        text = `Před ${minutes} ${minutes === 1 ? 'minutou' : 'minutami'}`;
    }

    lastUpdateEl.textContent = `Poslední aktualizace: ${text}`;
}

/**
 * Check for stale data
 */
function checkStaleData() {
    if (!lastUpdateTime) return;

    const now = new Date();
    const timeSinceUpdate = now - lastUpdateTime;
    const staleWarning = document.getElementById('stale-data-warning');

    if (timeSinceUpdate > STALE_DATA_THRESHOLD) {
        // Data is stale
        if (staleWarning) {
            staleWarning.style.display = 'block';
        }
        updateConnectionStatus('stale', 'Neaktuální data');
    } else {
        // Data is fresh
        if (staleWarning) {
            staleWarning.style.display = 'none';
        }
    }

    // Update relative time
    updateLastUpdateTime();
}

/**
 * Mark data as updated
 */
function markDataUpdated() {
    lastUpdateTime = new Date();
    updateLastUpdateTime();

    // Hide stale warning
    const staleWarning = document.getElementById('stale-data-warning');
    if (staleWarning) {
        staleWarning.style.display = 'none';
    }

    updateConnectionStatus('connected', 'Připojeno');
}

/**
 * Initialize WebSocket connection
 */
function initWebSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
        utils.showNotification('Připojeno k serveru', 'success');
        updateConnectionStatus('connected', 'Připojeno');

        // Start stale data checking
        if (staleDataCheckInterval) {
            clearInterval(staleDataCheckInterval);
        }
        staleDataCheckInterval = setInterval(checkStaleData, 5000); // Check every 5 seconds
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        utils.showNotification('Odpojeno od serveru', 'warning');
        updateConnectionStatus('disconnected', 'Odpojeno');

        // Stop stale data checking
        if (staleDataCheckInterval) {
            clearInterval(staleDataCheckInterval);
        }
    });

    socket.on('temperature_update', (data) => {
        updateTemperatureDisplay(data);
        updateTemperatureChart(data);
        markDataUpdated();
    });

    socket.on('status_update', (data) => {
        updateStatusDisplay(data);
        markDataUpdated();
    });

    socket.on('error', (error) => {
        console.error('WebSocket error:', error);
        utils.showNotification('Chyba komunikace', 'error');
        updateConnectionStatus('disconnected', 'Chyba');
    });
}

/**
 * Update temperature display
 */
function updateTemperatureDisplay(data) {
    // Update individual tank temperatures
    const temp1 = document.querySelector('#temp1 .temp-value');
    const temp2 = document.querySelector('#temp2 .temp-value');
    const temp3 = document.querySelector('#temp3 .temp-value');
    const tempAvg = document.querySelector('#temp-avg .temp-value');

    if (temp1) temp1.textContent = utils.formatTemperature(data.tank1);
    if (temp2) temp2.textContent = utils.formatTemperature(data.tank2);
    if (temp3) temp3.textContent = utils.formatTemperature(data.tank3);
    if (tempAvg) tempAvg.textContent = utils.formatTemperature(data.average);
}

/**
 * Update status indicators
 */
function updateStatusDisplay(data) {
    // Heating status
    const heatingStatus = document.getElementById('heating-status');
    const heatingText = document.getElementById('heating-text');

    if (heatingStatus) {
        if (data.heating) {
            heatingStatus.classList.add('active');
            heatingText.textContent = 'Zapnuto';
        } else {
            heatingStatus.classList.remove('active');
            heatingText.textContent = 'Vypnuto';
        }
    }

    // Pump status
    const pumpStatus = document.getElementById('pump-status');
    const pumpText = document.getElementById('pump-text');

    if (pumpStatus) {
        if (data.pump) {
            pumpStatus.classList.add('active');
            pumpText.textContent = 'Zapnuto';
        } else {
            pumpStatus.classList.remove('active');
            pumpText.textContent = 'Vypnuto';
        }
    }

    // Settings display
    utils.updateElement('setpoint', utils.formatTemperature(data.setpoint));
    utils.updateElement('hysteresis', utils.formatTemperature(data.hysteresis));

    // Manual override warning banner
    const warningBanner = document.getElementById('manual-override-warning');
    if (warningBanner) {
        if (data.manual_override) {
            warningBanner.style.display = 'block';
        } else {
            warningBanner.style.display = 'none';
        }
    }

    // Heating system disabled warning banner
    const heatingSystemWarning = document.getElementById('heating-system-disabled-warning');
    if (heatingSystemWarning) {
        // Show warning if heating system is disabled (and not in manual override mode)
        if (data.heating_system_enabled === false && !data.manual_override) {
            heatingSystemWarning.style.display = 'block';
        } else {
            heatingSystemWarning.style.display = 'none';
        }
    }
}

/**
 * Update temperature chart with new data
 */
function updateTemperatureChart(data) {
    const now = new Date().toLocaleTimeString('cs-CZ');

    // Add new data point
    temperatureHistory.labels.push(now);
    temperatureHistory.tank1.push(data.tank1);
    temperatureHistory.tank2.push(data.tank2);
    temperatureHistory.tank3.push(data.tank3);
    temperatureHistory.average.push(data.average);

    // Keep only last N points
    if (temperatureHistory.labels.length > MAX_HISTORY_POINTS) {
        temperatureHistory.labels.shift();
        temperatureHistory.tank1.shift();
        temperatureHistory.tank2.shift();
        temperatureHistory.tank3.shift();
        temperatureHistory.average.shift();
    }

    // Update chart
    if (temperatureChart) {
        temperatureChart.data.labels = temperatureHistory.labels;
        temperatureChart.data.datasets[0].data = temperatureHistory.tank1;
        temperatureChart.data.datasets[1].data = temperatureHistory.tank2;
        temperatureChart.data.datasets[2].data = temperatureHistory.tank3;
        temperatureChart.data.datasets[3].data = temperatureHistory.average;
        temperatureChart.update('none'); // Update without animation for smooth updates
    }
}

/**
 * Initialize temperature chart
 */
function initChart() {
    const ctx = document.getElementById('temperatureChart');
    if (!ctx) return;

    temperatureChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: temperatureHistory.labels,
            datasets: [
                {
                    label: 'Nádrž 1',
                    data: temperatureHistory.tank1,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Nádrž 2',
                    data: temperatureHistory.tank2,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Nádrž 3',
                    data: temperatureHistory.tank3,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Průměr',
                    data: temperatureHistory.average,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Teplota (°C)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Čas'
                    }
                }
            }
        }
    });
}

/**
 * Load historical temperature data from database
 */
async function loadHistoricalData() {
    try {
        // Fetch last 2 hours of averaged data (5-minute intervals)
        const response = await utils.apiCall('/api/history/average?hours=2&interval=5');

        if (response.success && response.data && response.data.length > 0) {
            // Clear existing data
            temperatureHistory.labels = [];
            temperatureHistory.tank1 = [];
            temperatureHistory.tank2 = [];
            temperatureHistory.tank3 = [];
            temperatureHistory.average = [];

            // Load historical data
            response.data.forEach(point => {
                const time = new Date(point.timestamp).toLocaleTimeString('cs-CZ', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
                temperatureHistory.labels.push(time);
                temperatureHistory.tank1.push(point.tank1 || null);
                temperatureHistory.tank2.push(point.tank2 || null);
                temperatureHistory.tank3.push(point.tank3 || null);
                temperatureHistory.average.push(point.average || null);
            });

            // Update chart with historical data
            if (temperatureChart) {
                temperatureChart.data.labels = temperatureHistory.labels;
                temperatureChart.data.datasets[0].data = temperatureHistory.tank1;
                temperatureChart.data.datasets[1].data = temperatureHistory.tank2;
                temperatureChart.data.datasets[2].data = temperatureHistory.tank3;
                temperatureChart.data.datasets[3].data = temperatureHistory.average;
                temperatureChart.update();
            }

            console.log('Historical data loaded:', response.data.length, 'points');
        }
    } catch (error) {
        console.error('Error loading historical data:', error);
        // Don't show notification - not critical for operation
    }
}

/**
 * Fetch initial data
 */
async function fetchInitialData() {
    try {
        // Fetch current temperature
        const tempData = await utils.apiCall('/api/temperature');
        updateTemperatureDisplay(tempData);
        updateTemperatureChart(tempData);

        // Fetch current status
        const statusData = await utils.apiCall('/api/status');
        updateStatusDisplay(statusData);

        // Mark data as updated (initialize timestamp)
        markDataUpdated();
    } catch (error) {
        console.error('Error fetching initial data:', error);
        utils.showNotification('Chyba načítání dat', 'error');
    }
}

/**
 * Update current time display
 */
function updateCurrentTime() {
    const now = new Date();

    const dateElement = document.getElementById('current-date');
    const timeElement = document.getElementById('current-time');

    if (dateElement) {
        dateElement.textContent = now.toLocaleDateString('cs-CZ', {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric'
        });
    }

    if (timeElement) {
        timeElement.textContent = now.toLocaleTimeString('cs-CZ', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

/**
 * Initialize dashboard
 */
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Dashboard initializing...');

    // Initialize chart
    initChart();

    // Load historical data from database
    await loadHistoricalData();

    // Fetch initial data
    fetchInitialData();

    // Initialize WebSocket for real-time updates
    initWebSocket();

    // Update current time immediately and then every second
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);

    // Refresh data periodically as fallback
    setInterval(fetchInitialData, 30000); // Every 30 seconds
});
