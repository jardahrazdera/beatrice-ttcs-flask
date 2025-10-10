/**
 * Settings JavaScript - Configuration and control
 */

// WebSocket connection
let socket;

/**
 * Initialize WebSocket connection
 */
function initWebSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('status_update', (data) => {
        updateCurrentStatus(data);
    });
}

/**
 * Update current status display
 */
function updateCurrentStatus(data) {
    // Update mode
    const modeElement = document.getElementById('current-mode');
    if (modeElement) {
        if (data.manual_override) {
            modeElement.textContent = 'Manuální';
            modeElement.classList.remove('active');
        } else {
            modeElement.textContent = 'Automatický';
            modeElement.classList.add('active');
        }
    }

    // Update heating status
    const heatingElement = document.getElementById('current-heating');
    if (heatingElement) {
        heatingElement.textContent = data.heating ? 'Zapnuto' : 'Vypnuto';
        if (data.heating) {
            heatingElement.classList.add('active');
        } else {
            heatingElement.classList.remove('active');
        }
    }

    // Update pump status
    const pumpElement = document.getElementById('current-pump');
    if (pumpElement) {
        pumpElement.textContent = data.pump ? 'Zapnuto' : 'Vypnuto';
        if (data.pump) {
            pumpElement.classList.add('active');
        } else {
            pumpElement.classList.remove('active');
        }
    }
}

/**
 * Load current settings
 */
async function loadSettings() {
    try {
        const response = await utils.apiCall('/api/settings');

        // Temperature settings
        document.getElementById('setpoint').value = response.setpoint || 60;
        document.getElementById('hysteresis').value = response.hysteresis || 2;
        document.getElementById('max-temp').value = response.max_temperature || 85;

        // Pump settings
        document.getElementById('pump-delay').value = response.pump_delay || 60;

        // System settings
        document.getElementById('update-interval').value = response.update_interval || 5;
        document.getElementById('sensor-timeout').value = response.sensor_timeout || 30;

        // Manual override
        const manualOverride = document.getElementById('manual-override');
        const manualHeating = document.getElementById('manual-heating');
        const manualControls = document.getElementById('manual-controls');

        manualOverride.checked = response.manual_override || false;
        manualHeating.checked = response.manual_heating || false;
        manualControls.style.display = response.manual_override ? 'block' : 'none';

        // Hardware config
        utils.updateElement('relay-heating', response.relay_heating || 1);
        utils.updateElement('relay-pump', response.relay_pump || 2);
        utils.updateElement('sensor-count', response.sensor_count || '--');

    } catch (error) {
        console.error('Error loading settings:', error);
        utils.showNotification('Chyba načítání nastavení', 'error');
    }
}

/**
 * Save temperature settings
 */
async function saveTemperatureSettings(event) {
    event.preventDefault();

    const formData = {
        setpoint: parseFloat(document.getElementById('setpoint').value),
        hysteresis: parseFloat(document.getElementById('hysteresis').value),
        max_temperature: parseFloat(document.getElementById('max-temp').value)
    };

    try {
        await utils.apiCall('/api/settings/temperature', 'POST', formData);
        utils.showNotification('Nastavení teploty uloženo', 'success');
    } catch (error) {
        console.error('Error saving temperature settings:', error);
        utils.showNotification('Chyba při ukládání nastavení', 'error');
    }
}

/**
 * Save pump settings
 */
async function savePumpSettings(event) {
    event.preventDefault();

    const formData = {
        pump_delay: parseInt(document.getElementById('pump-delay').value)
    };

    try {
        await utils.apiCall('/api/settings/pump', 'POST', formData);
        utils.showNotification('Nastavení čerpadla uloženo', 'success');
    } catch (error) {
        console.error('Error saving pump settings:', error);
        utils.showNotification('Chyba při ukládání nastavení', 'error');
    }
}

/**
 * Save system settings
 */
async function saveSystemSettings(event) {
    event.preventDefault();

    const formData = {
        update_interval: parseInt(document.getElementById('update-interval').value),
        sensor_timeout: parseInt(document.getElementById('sensor-timeout').value)
    };

    try {
        await utils.apiCall('/api/settings/system', 'POST', formData);
        utils.showNotification('Systémová nastavení uložena', 'success');
    } catch (error) {
        console.error('Error saving system settings:', error);
        utils.showNotification('Chyba při ukládání nastavení', 'error');
    }
}

/**
 * Handle manual override toggle
 */
function toggleManualOverride() {
    const manualOverride = document.getElementById('manual-override');
    const manualControls = document.getElementById('manual-controls');

    manualControls.style.display = manualOverride.checked ? 'block' : 'none';
}

/**
 * Save manual override settings
 */
async function saveManualOverride(event) {
    event.preventDefault();

    const manualOverride = document.getElementById('manual-override').checked;
    const manualHeating = document.getElementById('manual-heating').checked;

    if (manualOverride) {
        const confirmed = confirm(
            'Varování: Aktivace manuálního režimu deaktivuje automatické řízení. ' +
            'Systém nebude automaticky regulovat teplotu. Pokračovat?'
        );

        if (!confirmed) {
            return;
        }
    }

    const formData = {
        manual_override: manualOverride,
        manual_heating: manualHeating
    };

    try {
        await utils.apiCall('/api/settings/manual', 'POST', formData);
        utils.showNotification('Manuální režim ' + (manualOverride ? 'aktivován' : 'deaktivován'), 'warning');
    } catch (error) {
        console.error('Error saving manual override:', error);
        utils.showNotification('Chyba při ukládání nastavení', 'error');
    }
}

/**
 * Load database statistics
 */
async function loadDatabaseStats() {
    try {
        const response = await utils.apiCall('/api/database/stats');

        // Update database size
        const sizeInMB = (response.size / (1024 * 1024)).toFixed(2);
        utils.updateElement('db-size', `${sizeInMB} MB`);

        // Update record count
        const totalRecords = response.temperature_records + response.event_records + response.control_records;
        utils.updateElement('db-records', totalRecords.toLocaleString('cs-CZ'));

    } catch (error) {
        console.error('Error loading database stats:', error);
        utils.updateElement('db-size', '--');
        utils.updateElement('db-records', '--');
    }
}

/**
 * Delete all database data
 */
async function deleteDatabase() {
    // First confirmation
    const confirmed1 = confirm(
        'VAROVÁNÍ: Tato akce smaže všechna historická data z databáze!\n\n' +
        'Budou smazány:\n' +
        '- Všechny záznamy teplot\n' +
        '- Všechny události systému\n' +
        '- Všechna data řízení\n\n' +
        'Tato akce je NEVRATNÁ!\n\n' +
        'Opravdu chcete pokračovat?'
    );

    if (!confirmed1) {
        return;
    }

    // Second confirmation
    const confirmed2 = confirm(
        'POSLEDNÍ VAROVÁNÍ!\n\n' +
        'Jste si absolutně jisti, že chcete smazat všechna data?\n\n' +
        'Tuto akci nelze vrátit zpět!'
    );

    if (!confirmed2) {
        return;
    }

    try {
        const response = await utils.apiCall('/api/database/delete', 'POST');

        if (response.success) {
            utils.showNotification(
                `Databáze byla úspěšně vymazána. Smazáno: ${response.deleted.temperature} teplot, ` +
                `${response.deleted.events} událostí, ${response.deleted.actions} akcí.`,
                'success'
            );

            // Reload database stats
            loadDatabaseStats();
        } else {
            utils.showNotification('Chyba při mazání databáze', 'error');
        }
    } catch (error) {
        console.error('Error deleting database:', error);
        utils.showNotification('Chyba při mazání databáze: ' + error.message, 'error');
    }
}

/**
 * Initialize settings page
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Settings page initializing...');

    // Load current settings
    loadSettings();

    // Load database statistics
    loadDatabaseStats();

    // Initialize WebSocket
    initWebSocket();

    // Attach form handlers
    const tempForm = document.getElementById('temp-settings-form');
    if (tempForm) {
        tempForm.addEventListener('submit', saveTemperatureSettings);
    }

    const pumpForm = document.getElementById('pump-settings-form');
    if (pumpForm) {
        pumpForm.addEventListener('submit', savePumpSettings);
    }

    const systemForm = document.getElementById('system-settings-form');
    if (systemForm) {
        systemForm.addEventListener('submit', saveSystemSettings);
    }

    const manualForm = document.getElementById('manual-override-form');
    if (manualForm) {
        manualForm.addEventListener('submit', saveManualOverride);
    }

    // Manual override toggle
    const manualOverride = document.getElementById('manual-override');
    if (manualOverride) {
        manualOverride.addEventListener('change', toggleManualOverride);
    }

    // Delete database button
    const deleteDatabaseBtn = document.getElementById('delete-database-btn');
    if (deleteDatabaseBtn) {
        deleteDatabaseBtn.addEventListener('click', deleteDatabase);
    }

    // Refresh status periodically
    setInterval(async () => {
        try {
            const statusData = await utils.apiCall('/api/status');
            updateCurrentStatus(statusData);
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }, 10000); // Every 10 seconds
});
