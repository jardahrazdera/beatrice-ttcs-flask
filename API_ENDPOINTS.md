# API Endpoints Documentation

## Complete API Endpoints List for Postman Testing

This document contains **29 total endpoints** (25 HTTP + 4 WebSocket events) in the Flask application.

---

## 📄 Web Pages (HTML Routes)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Required | Main dashboard page |
| GET | `/login` | None | Login page |
| POST | `/login` | None | Process login (form: username, password) |
| GET | `/logout` | None | Logout and disable manual override |
| GET | `/history` | Required | History/statistics page |
| GET | `/settings` | Required | Settings page |

---

## 🏥 System Status & Monitoring

### GET /health
- **Authentication**: None (CSRF exempt)
- **Description**: Health check endpoint for monitoring systems
- **Response**: JSON
  ```json
  {
    "status": "healthy|degraded|unhealthy",
    "service": "water-tank-control",
    "timestamp": "ISO-8601 timestamp",
    "controller_active": true/false,
    "sensor_count": 3,
    "database_connected": true/false,
    "database_size_bytes": 1234567
  }
  ```
- **Status Codes**: 200 (healthy), 503 (degraded/unhealthy)

### GET /api/temperature
- **Authentication**: Required
- **Description**: Get current temperature readings from all tanks
- **Response**: JSON
  ```json
  {
    "tank1": 62.5,
    "tank2": 63.0,
    "tank3": 62.8,
    "average": 62.77
  }
  ```

### GET /api/status
- **Authentication**: Required
- **Description**: Get current system status
- **Response**: JSON
  ```json
  {
    "heating": true/false,
    "pump": true/false,
    "setpoint": 60.0,
    "hysteresis": 2.0,
    "manual_override": false,
    "heating_system_enabled": true
  }
  ```

---

## ⚙️ Settings Management

### GET /api/settings
- **Authentication**: Required
- **Description**: Load current system settings
- **Response**: JSON with all current settings including `sensor_count`

### POST /api/settings/temperature
- **Authentication**: Required
- **Description**: Save temperature control settings
- **Request Body**: JSON
  ```json
  {
    "setpoint": 60.0,
    "hysteresis": 2.0,
    "max_temperature": 85.0
  }
  ```
- **Validation**:
  - `setpoint`: 5-85°C
  - `hysteresis`: 0.5-10°C
  - `max_temperature`: 60-95°C
- **Response**: JSON
  ```json
  {
    "success": true,
    "message": "Settings saved"
  }
  ```
- **Status Codes**: 200 (success), 400 (validation error), 500 (server error)

### POST /api/settings/pump
- **Authentication**: Required
- **Description**: Save pump control settings
- **Request Body**: JSON
  ```json
  {
    "pump_delay": 60
  }
  ```
- **Validation**: `pump_delay`: 0-300 seconds
- **Response**: JSON (success/error)
- **Status Codes**: 200 (success), 400 (validation error), 500 (server error)

### POST /api/settings/system
- **Authentication**: Required
- **Description**: Save system operational settings
- **Request Body**: JSON
  ```json
  {
    "update_interval": 5,
    "sensor_timeout": 30
  }
  ```
- **Validation**:
  - `update_interval`: 1-60 seconds
  - `sensor_timeout`: 5-120 seconds
- **Response**: JSON (success/error)
- **Status Codes**: 200 (success), 400 (validation error), 500 (server error)

### POST /api/settings/manual
- **Authentication**: Required + **Super Admin**
- **Description**: Enable/disable manual override mode (SUPER ADMIN ONLY)
- **Request Body**: JSON
  ```json
  {
    "super_admin_password": "password",
    "manual_override": true,
    "manual_heating": true,
    "manual_pump": false
  }
  ```
- **Response**: JSON
  ```json
  {
    "success": true,
    "message": "Manual override updated"
  }
  ```
- **Status Codes**: 200 (success), 403 (invalid super admin password), 500 (server error)

### POST /api/settings/heating-system
- **Authentication**: Required
- **Description**: Enable/disable heating system (available to all authenticated users)
- **Request Body**: JSON
  ```json
  {
    "enabled": true
  }
  ```
- **Response**: JSON
  ```json
  {
    "success": true,
    "message": "Heating system enabled|disabled",
    "heating_system_enabled": true
  }
  ```
- **Status Codes**: 200 (success), 400 (missing parameter), 500 (server error)

---

## 📊 History & Statistics

### GET /api/history/temperature
- **Authentication**: Required
- **Description**: Get temperature history for specified time period
- **Query Parameters**:
  - `hours`: integer (default: 24) - how many hours of history
  - `tank`: integer (optional) - specific tank number (1, 2, or 3)
- **Response**: JSON
  ```json
  {
    "success": true,
    "data": [...]
  }
  ```

### GET /api/history/average
- **Authentication**: Required
- **Description**: Get averaged temperature history
- **Query Parameters**:
  - `hours`: integer (default: 24) - time period
  - `interval`: integer (default: 5) - averaging interval in minutes
- **Response**: JSON
  ```json
  {
    "success": true,
    "data": [...]
  }
  ```

### GET /api/history/average/range
- **Authentication**: Required
- **Description**: Get averaged temperature history for custom date range
- **Query Parameters**:
  - `from`: datetime string (YYYY-MM-DDTHH:MM format)
  - `to`: datetime string (YYYY-MM-DDTHH:MM format)
  - `interval`: integer (default: 5) - averaging interval in minutes
- **Response**: JSON
  ```json
  {
    "success": true,
    "data": [...]
  }
  ```
- **Status Codes**: 200 (success), 400 (invalid date format/range)

### GET /api/history/events
- **Authentication**: Required
- **Description**: Get system event history
- **Query Parameters**:
  - `limit`: integer (default: 100) - max number of events
  - `type`: string (optional) - filter by event type
- **Response**: JSON
  ```json
  {
    "success": true,
    "data": [...]
  }
  ```

### GET /api/history/events/range
- **Authentication**: Required
- **Description**: Get system events for custom date range
- **Query Parameters**:
  - `from`: datetime string (YYYY-MM-DDTHH:MM format)
  - `to`: datetime string (YYYY-MM-DDTHH:MM format)
  - `type`: string (optional) - filter by event type
- **Response**: JSON (success/error with data)
- **Status Codes**: 200 (success), 400 (invalid date format/range)

### GET /api/history/control
- **Authentication**: Required
- **Description**: Get control action history
- **Query Parameters**:
  - `hours`: integer (default: 24) - time period
- **Response**: JSON
  ```json
  {
    "success": true,
    "data": [...]
  }
  ```

### GET /api/history/control/range
- **Authentication**: Required
- **Description**: Get control action history for custom date range
- **Query Parameters**:
  - `from`: datetime string (YYYY-MM-DDTHH:MM format)
  - `to`: datetime string (YYYY-MM-DDTHH:MM format)
- **Response**: JSON (success/error with data)
- **Status Codes**: 200 (success), 400 (invalid date format/range)

### GET /api/statistics
- **Authentication**: Required
- **Description**: Get statistical summary
- **Query Parameters**:
  - `hours`: integer (default: 24) - time period for statistics
- **Response**: JSON
  ```json
  {
    "success": true,
    "data": {...}
  }
  ```

---

## 💾 Database Management

### GET /api/database/stats
- **Authentication**: Required
- **Description**: Get database statistics and information
- **Response**: JSON with database info (size, record counts, etc.)

### POST /api/database/delete
- **Authentication**: Required + **Super Admin**
- **Description**: Delete ALL database data (SUPER ADMIN ONLY)
- **Request Body**: JSON
  ```json
  {
    "super_admin_password": "password"
  }
  ```
- **Response**: JSON
  ```json
  {
    "success": true,
    "deleted": {...},
    "message": "All database data has been deleted"
  }
  ```
- **Status Codes**: 200 (success), 403 (invalid super admin password), 500 (server error)

---

## 🔌 WebSocket Events

### Connection URL
```
ws://localhost:8080/ws
```

### Events

#### connect (Client → Server)
- **Description**: Handle WebSocket connection
- **Server Emits**: `status` event with connection message
- **Emitted Data**:
  ```json
  {
    "message": "Connected to server"
  }
  ```

#### disconnect (Client → Server)
- **Description**: Handle WebSocket disconnection
- **No data emitted**

#### temperature_update (Server → Client)
- **Description**: Server broadcasts temperature updates periodically
- **Emitted Data**:
  ```json
  {
    "tank1": 62.5,
    "tank2": 63.0,
    "tank3": 62.8,
    "average": 62.77
  }
  ```
- **Broadcast Interval**: Based on `update_interval` setting (default: 5 seconds)

#### status_update (Server → Client)
- **Description**: Server broadcasts system status updates periodically
- **Emitted Data**:
  ```json
  {
    "heating": true,
    "pump": false,
    "setpoint": 60.0,
    "hysteresis": 2.0,
    "manual_override": false,
    "heating_system_enabled": true
  }
  ```
- **Broadcast Interval**: Based on `update_interval` setting (default: 5 seconds)

---

## 📋 Example Postman Requests

### 1. Login (POST /login)
```
Method: POST
URL: http://localhost:5000/login
Body Type: x-www-form-urlencoded

Body:
username: admin
password: your_password
```

### 2. Get Temperature (GET /api/temperature)
```
Method: GET
URL: http://localhost:5000/api/temperature

Headers:
Cookie: session=<your_session_cookie>
```

### 3. Set Temperature (POST /api/settings/temperature)
```
Method: POST
URL: http://localhost:5000/api/settings/temperature
Content-Type: application/json

Headers:
Cookie: session=<your_session_cookie>

Body (JSON):
{
  "setpoint": 65.0,
  "hysteresis": 2.5,
  "max_temperature": 85.0
}
```

### 4. Enable Heating System (POST /api/settings/heating-system)
```
Method: POST
URL: http://localhost:5000/api/settings/heating-system
Content-Type: application/json

Headers:
Cookie: session=<your_session_cookie>

Body (JSON):
{
  "enabled": true
}
```

### 5. Get History Range (GET /api/history/average/range)
```
Method: GET
URL: http://localhost:5000/api/history/average/range

Headers:
Cookie: session=<your_session_cookie>

Query Parameters:
from: 2025-11-01T00:00
to: 2025-11-06T23:59
interval: 10
```

### 6. Health Check (GET /health)
```
Method: GET
URL: http://localhost:5000/health

No authentication required
```

### 7. Get System Status (GET /api/status)
```
Method: GET
URL: http://localhost:5000/api/status

Headers:
Cookie: session=<your_session_cookie>
```

---

## 🔐 Authentication Notes

- **Session-based authentication**: After successful login, a session cookie is returned
- **Cookie handling**: Save the session cookie from login response and include it in subsequent requests
- **Super Admin operations**: Require `super_admin_password` in request body
- **CSRF protection**: Disabled by default for JavaScript API calls
- **Auto-logout safety**: Manual override is automatically disabled on logout

---

## 📊 Summary

- **Total Endpoints**: 29 (25 HTTP + 4 WebSocket)
- **HTTP Methods**:
  - GET: 19 endpoints
  - POST: 10 endpoints
- **Authentication Levels**:
  - Public (no auth): 3 endpoints (login, logout, health)
  - Authenticated users: 22 endpoints
  - Super Admin only: 2 endpoints (manual override, database delete)

---

## 📍 File References

- Main routes: `app.py:63-595`
- Authentication decorators: Uses `@requires_auth` and `@requires_super_admin`
- Super Admin operations require `super_admin_password` in request body
