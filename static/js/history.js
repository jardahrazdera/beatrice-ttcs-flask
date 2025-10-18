/**
 * History page JavaScript - Historical data viewing and analysis
 */

// Chart instance
let historyChart;

// Pagination state
let temperatureData = [];
let eventsData = [];
let controlData = [];
let currentTempPage = 1;
let currentEventsPage = 1;
let currentControlPage = 1;
const rowsPerPage = 50;

/**
 * Initialize tab switching
 */
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked tab
            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');

            // Load data for the selected tab if not already loaded
            loadTabData(tabName);
        });
    });
}

/**
 * Load data for specific tab when it becomes active
 */
function loadTabData(tabName) {
    switch(tabName) {
        case 'temperature':
            // Temperature data is already loaded on page load
            break;
        case 'events':
            loadEvents();
            break;
        case 'control':
            loadControlHistory();
            break;
        case 'statistics':
            loadStatistics();
            break;
    }
}

/**
 * Initialize temperature history chart
 */
function initHistoryChart() {
    const ctx = document.getElementById('historyChart');
    if (!ctx) return;

    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Nádrž 1',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Nádrž 2',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Nádrž 3',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Průměr',
                    data: [],
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
 * Load and display temperature history
 */
async function loadTemperatureHistory() {
    try {
        const hours = document.getElementById('temp-hours').value;
        const interval = document.getElementById('temp-interval').value;

        // Add cache buster to prevent browser caching
        const cacheBuster = new Date().getTime();
        const response = await utils.apiCall(`/api/history/average?hours=${hours}&interval=${interval}&_=${cacheBuster}`);

        if (response.success && response.data) {
            // Store data for pagination - REVERSE to show newest first
            temperatureData = [...response.data].reverse();
            currentTempPage = 1;

            // Update chart with all data (keep chronological order - oldest to newest)
            updateTemperatureChart(response.data);

            // Update table with first page (newest records first)
            updateTemperatureTable();
        }
    } catch (error) {
        console.error('Error loading temperature history:', error);
        utils.showNotification('Chyba načítání historie teplot', 'error');
    }
}

/**
 * Update temperature chart with data
 */
function updateTemperatureChart(data) {
    const labels = [];
    const tank1Data = [];
    const tank2Data = [];
    const tank3Data = [];
    const avgData = [];

    data.forEach(point => {
        // Parse UTC timestamp and convert to CET
        const utcDate = new Date(point.timestamp + 'Z'); // Add Z to indicate UTC
        const time = utcDate.toLocaleString('cs-CZ', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Europe/Prague'
        });
        labels.push(time);
        tank1Data.push(point.tank1);
        tank2Data.push(point.tank2);
        tank3Data.push(point.tank3);
        avgData.push(point.average);
    });

    if (historyChart) {
        historyChart.data.labels = labels;
        historyChart.data.datasets[0].data = tank1Data;
        historyChart.data.datasets[1].data = tank2Data;
        historyChart.data.datasets[2].data = tank3Data;
        historyChart.data.datasets[3].data = avgData;
        historyChart.update();
    }
}

/**
 * Update temperature table with paginated data
 */
function updateTemperatureTable() {
    const tbody = document.getElementById('temp-table-body');
    if (!tbody) return;

    if (temperatureData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty">Žádná data k zobrazení</td></tr>';
        updatePaginationControls(0);
        return;
    }

    // Calculate pagination
    const totalPages = Math.ceil(temperatureData.length / rowsPerPage);
    const startIndex = (currentTempPage - 1) * rowsPerPage;
    const endIndex = Math.min(startIndex + rowsPerPage, temperatureData.length);
    const pageData = temperatureData.slice(startIndex, endIndex);

    // Update table with current page data
    tbody.innerHTML = pageData.map(point => {
        // Parse UTC timestamp and convert to CET
        const utcDate = new Date(point.timestamp + 'Z'); // Add Z to indicate UTC
        const time = utcDate.toLocaleString('cs-CZ', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Europe/Prague'
        });
        return `
            <tr>
                <td>${time}</td>
                <td>${utils.formatTemperature(point.tank1)}</td>
                <td>${utils.formatTemperature(point.tank2)}</td>
                <td>${utils.formatTemperature(point.tank3)}</td>
                <td><strong>${utils.formatTemperature(point.average)}</strong></td>
            </tr>
        `;
    }).join('');

    // Update pagination controls
    updatePaginationControls(totalPages);
}

/**
 * Update pagination controls
 */
function updatePaginationControls(totalPages) {
    const paginationDiv = document.getElementById('temp-pagination');
    if (!paginationDiv) return;

    if (totalPages <= 1) {
        paginationDiv.style.display = 'none';
        return;
    }

    paginationDiv.style.display = 'flex';

    const startRecord = ((currentTempPage - 1) * rowsPerPage) + 1;
    const endRecord = Math.min(currentTempPage * rowsPerPage, temperatureData.length);

    paginationDiv.innerHTML = `
        <button class="btn btn-secondary" id="prev-page" ${currentTempPage === 1 ? 'disabled' : ''}>
            ← Předchozí
        </button>
        <span class="pagination-info">
            Stránka ${currentTempPage} z ${totalPages} (zobrazeno ${startRecord}-${endRecord} z ${temperatureData.length} záznamů)
        </span>
        <button class="btn btn-secondary" id="next-page" ${currentTempPage === totalPages ? 'disabled' : ''}>
            Další →
        </button>
    `;

    // Add event listeners
    document.getElementById('prev-page')?.addEventListener('click', () => {
        if (currentTempPage > 1) {
            currentTempPage--;
            updateTemperatureTable();
        }
    });

    document.getElementById('next-page')?.addEventListener('click', () => {
        if (currentTempPage < totalPages) {
            currentTempPage++;
            updateTemperatureTable();
        }
    });
}

/**
 * Export temperature data to CSV
 */
function exportTemperatureCSV() {
    const hours = document.getElementById('temp-hours').value;
    const interval = document.getElementById('temp-interval').value;

    // Create CSV content from current table
    const table = document.getElementById('temp-table');
    const rows = table.querySelectorAll('tr');
    let csv = [];

    rows.forEach(row => {
        const cells = row.querySelectorAll('th, td');
        const rowData = Array.from(cells).map(cell => `"${cell.textContent.trim()}"`);
        csv.push(rowData.join(','));
    });

    // Create download link
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `teploty_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    utils.showNotification('CSV soubor exportován', 'success');
}

/**
 * Load and display system events
 */
async function loadEvents() {
    try {
        // Remove limit parameter, fetch all events up to a reasonable maximum
        const eventType = document.getElementById('event-type').value;

        // Add cache buster
        const cacheBuster = new Date().getTime();
        let url = `/api/history/events?limit=1000&_=${cacheBuster}`;
        if (eventType) {
            url += `&type=${eventType}`;
        }

        const response = await utils.apiCall(url);

        if (response.success && response.data) {
            eventsData = response.data;
            currentEventsPage = 1;
            updateEventsTable();
        }
    } catch (error) {
        console.error('Error loading events:', error);
        utils.showNotification('Chyba načítání událostí', 'error');
    }
}

/**
 * Update events table with paginated data
 */
function updateEventsTable() {
    const tbody = document.getElementById('events-table-body');
    if (!tbody) return;

    if (eventsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="empty">Žádné události k zobrazení</td></tr>';
        updateEventsPaginationControls(0);
        return;
    }

    // Calculate pagination
    const totalPages = Math.ceil(eventsData.length / rowsPerPage);
    const startIndex = (currentEventsPage - 1) * rowsPerPage;
    const endIndex = Math.min(startIndex + rowsPerPage, eventsData.length);
    const pageData = eventsData.slice(startIndex, endIndex);

    tbody.innerHTML = pageData.map(event => {
        // Parse UTC timestamp and convert to CET
        const utcDate = new Date(event.timestamp + 'Z');
        const time = utcDate.toLocaleString('cs-CZ', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZone: 'Europe/Prague'
        });
        const typeClass = event.event_type === 'error' ? 'badge-danger' :
                         event.event_type === 'warning' ? 'badge-warning' :
                         'badge-info';

        return `
            <tr>
                <td>${time}</td>
                <td><span class="badge ${typeClass}">${event.event_type}</span></td>
                <td>${event.description}</td>
            </tr>
        `;
    }).join('');

    // Update pagination controls
    updateEventsPaginationControls(totalPages);
}

/**
 * Update events pagination controls
 */
function updateEventsPaginationControls(totalPages) {
    const paginationDiv = document.getElementById('events-pagination');
    if (!paginationDiv) return;

    if (totalPages <= 1) {
        paginationDiv.style.display = 'none';
        return;
    }

    paginationDiv.style.display = 'flex';

    const startRecord = ((currentEventsPage - 1) * rowsPerPage) + 1;
    const endRecord = Math.min(currentEventsPage * rowsPerPage, eventsData.length);

    paginationDiv.innerHTML = `
        <button class="btn btn-secondary" id="prev-events-page" ${currentEventsPage === 1 ? 'disabled' : ''}>
            ← Předchozí
        </button>
        <span class="pagination-info">
            Stránka ${currentEventsPage} z ${totalPages} (zobrazeno ${startRecord}-${endRecord} z ${eventsData.length} záznamů)
        </span>
        <button class="btn btn-secondary" id="next-events-page" ${currentEventsPage === totalPages ? 'disabled' : ''}>
            Další →
        </button>
    `;

    // Add event listeners
    document.getElementById('prev-events-page')?.addEventListener('click', () => {
        if (currentEventsPage > 1) {
            currentEventsPage--;
            updateEventsTable();
        }
    });

    document.getElementById('next-events-page')?.addEventListener('click', () => {
        if (currentEventsPage < totalPages) {
            currentEventsPage++;
            updateEventsTable();
        }
    });
}

/**
 * Load and display control actions history
 */
async function loadControlHistory() {
    try {
        const hours = document.getElementById('control-hours').value;
        // Add cache buster
        const cacheBuster = new Date().getTime();
        const response = await utils.apiCall(`/api/history/control?hours=${hours}&_=${cacheBuster}`);

        if (response.success && response.data) {
            controlData = response.data;
            currentControlPage = 1;
            updateControlTable();
        }
    } catch (error) {
        console.error('Error loading control history:', error);
        utils.showNotification('Chyba načítání historie řízení', 'error');
    }
}

/**
 * Update control actions table with paginated data
 */
function updateControlTable() {
    const tbody = document.getElementById('control-table-body');
    if (!tbody) return;

    if (controlData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty">Žádné akce k zobrazení</td></tr>';
        updateControlPaginationControls(0);
        return;
    }

    // Calculate pagination
    const totalPages = Math.ceil(controlData.length / rowsPerPage);
    const startIndex = (currentControlPage - 1) * rowsPerPage;
    const endIndex = Math.min(startIndex + rowsPerPage, controlData.length);
    const pageData = controlData.slice(startIndex, endIndex);

    tbody.innerHTML = pageData.map(action => {
        // Parse UTC timestamp and convert to CET
        const utcDate = new Date(action.timestamp + 'Z');
        const time = utcDate.toLocaleString('cs-CZ', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZone: 'Europe/Prague'
        });
        const heatingIcon = action.heating_state ? '🔥 Zapnuto' : '❄️ Vypnuto';
        const pumpIcon = action.pump_state ? '▶️ Zapnuto' : '⏸️ Vypnuto';

        return `
            <tr>
                <td>${time}</td>
                <td><span class="badge badge-info">${action.action_type}</span></td>
                <td>${heatingIcon}</td>
                <td>${pumpIcon}</td>
                <td>${utils.formatTemperature(action.average_temperature)}</td>
                <td>${utils.formatTemperature(action.setpoint)}</td>
            </tr>
        `;
    }).join('');

    // Update pagination controls
    updateControlPaginationControls(totalPages);
}

/**
 * Update control history pagination controls
 */
function updateControlPaginationControls(totalPages) {
    const paginationDiv = document.getElementById('control-pagination');
    if (!paginationDiv) return;

    if (totalPages <= 1) {
        paginationDiv.style.display = 'none';
        return;
    }

    paginationDiv.style.display = 'flex';

    const startRecord = ((currentControlPage - 1) * rowsPerPage) + 1;
    const endRecord = Math.min(currentControlPage * rowsPerPage, controlData.length);

    paginationDiv.innerHTML = `
        <button class="btn btn-secondary" id="prev-control-page" ${currentControlPage === 1 ? 'disabled' : ''}>
            ← Předchozí
        </button>
        <span class="pagination-info">
            Stránka ${currentControlPage} z ${totalPages} (zobrazeno ${startRecord}-${endRecord} z ${controlData.length} záznamů)
        </span>
        <button class="btn btn-secondary" id="next-control-page" ${currentControlPage === totalPages ? 'disabled' : ''}>
            Další →
        </button>
    `;

    // Add event listeners
    document.getElementById('prev-control-page')?.addEventListener('click', () => {
        if (currentControlPage > 1) {
            currentControlPage--;
            updateControlTable();
        }
    });

    document.getElementById('next-control-page')?.addEventListener('click', () => {
        if (currentControlPage < totalPages) {
            currentControlPage++;
            updateControlTable();
        }
    });
}

/**
 * Load and display statistics
 */
async function loadStatistics() {
    try {
        const hours = document.getElementById('stats-hours').value;
        // Add cache buster
        const cacheBuster = new Date().getTime();
        const response = await utils.apiCall(`/api/statistics?hours=${hours}&_=${cacheBuster}`);

        if (response.success && response.data) {
            updateStatistics(response.data);
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
        utils.showNotification('Chyba načítání statistik', 'error');
    }
}

/**
 * Update statistics display with data
 */
function updateStatistics(data) {
    // Overall statistics
    utils.updateElement('stat-avg-temp', utils.formatTemperature(data.overall.avg_temperature));
    utils.updateElement('stat-min-temp', utils.formatTemperature(data.overall.min_temperature));
    utils.updateElement('stat-max-temp', utils.formatTemperature(data.overall.max_temperature));
    utils.updateElement('stat-reading-count', data.overall.reading_count || '0');

    // Control statistics
    const heatingHours = (data.control.heating_on_time / 3600).toFixed(1);
    const pumpHours = (data.control.pump_on_time / 3600).toFixed(1);
    const heatingPercent = ((data.control.heating_on_time / (parseInt(document.getElementById('stats-hours').value) * 3600)) * 100).toFixed(1);

    utils.updateElement('stat-heating-time', heatingHours);
    utils.updateElement('stat-pump-time', pumpHours);
    utils.updateElement('stat-heating-cycles', data.control.heating_cycles || '0');
    utils.updateElement('stat-heating-percent', heatingPercent);

    // Tank-specific statistics table
    updateStatisticsTable(data.tanks);
}

/**
 * Update statistics table with per-tank data
 */
function updateStatisticsTable(tanks) {
    const tbody = document.getElementById('stats-table-body');
    if (!tbody) return;

    if (!tanks || tanks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty">Žádná data k zobrazení</td></tr>';
        return;
    }

    tbody.innerHTML = tanks.map(tank => `
        <tr>
            <td>Nádrž ${tank.tank_number}</td>
            <td>${utils.formatTemperature(tank.avg_temperature)}</td>
            <td>${utils.formatTemperature(tank.min_temperature)}</td>
            <td>${utils.formatTemperature(tank.max_temperature)}</td>
            <td>${tank.reading_count || 0}</td>
        </tr>
    `).join('');
}

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('History page initializing...');

    // Initialize tabs
    initTabs();

    // Initialize chart
    initHistoryChart();

    // Load initial data for temperature tab
    loadTemperatureHistory();

    // Event listeners for temperature history
    document.getElementById('refresh-temp')?.addEventListener('click', loadTemperatureHistory);
    document.getElementById('export-temp')?.addEventListener('click', exportTemperatureCSV);
    document.getElementById('temp-hours')?.addEventListener('change', loadTemperatureHistory);
    document.getElementById('temp-interval')?.addEventListener('change', loadTemperatureHistory);

    // Event listeners for events tab
    document.getElementById('refresh-events')?.addEventListener('click', loadEvents);
    document.getElementById('event-type')?.addEventListener('change', loadEvents);

    // Event listeners for control tab
    document.getElementById('refresh-control')?.addEventListener('click', loadControlHistory);
    document.getElementById('control-hours')?.addEventListener('change', loadControlHistory);

    // Event listeners for statistics tab
    document.getElementById('refresh-stats')?.addEventListener('click', loadStatistics);
    document.getElementById('stats-hours')?.addEventListener('change', loadStatistics);

    console.log('History page initialized');
});
