"""
Database module for historical temperature data storage.

This module handles SQLite database operations for storing and retrieving
temperature readings, system events, and control actions.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager


class Database:
    """SQLite database handler for historical data."""

    def __init__(self, db_path: str = 'data.db'):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()

    @staticmethod
    def _get_utc_now() -> datetime:
        """Get current UTC time (SQLite uses UTC for CURRENT_TIMESTAMP)."""
        return datetime.utcnow()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Temperature readings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temperature_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sensor_id TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    tank_number INTEGER
                )
            ''')

            # System events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    data TEXT
                )
            ''')

            # Control actions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS control_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action_type TEXT NOT NULL,
                    heating_state BOOLEAN,
                    pump_state BOOLEAN,
                    average_temperature REAL,
                    setpoint REAL
                )
            ''')

            # Create indices for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_temp_timestamp
                ON temperature_readings(timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp
                ON system_events(timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_actions_timestamp
                ON control_actions(timestamp)
            ''')

            self.logger.info('Database schema initialized')

    def insert_temperature_reading(self, sensor_id: str, temperature: float,
                                   tank_number: Optional[int] = None):
        """
        Insert temperature reading into database.

        Args:
            sensor_id: Sensor identifier
            temperature: Temperature value in Celsius
            tank_number: Tank number (1-3) or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO temperature_readings (sensor_id, temperature, tank_number)
                    VALUES (?, ?, ?)
                ''', (sensor_id, temperature, tank_number))

        except Exception as e:
            self.logger.error(f"Error inserting temperature reading: {e}")

    def insert_multiple_readings(self, readings: List[Tuple[str, float, Optional[int]]]):
        """
        Insert multiple temperature readings in batch.

        Args:
            readings: List of (sensor_id, temperature, tank_number) tuples
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT INTO temperature_readings (sensor_id, temperature, tank_number)
                    VALUES (?, ?, ?)
                ''', readings)

        except Exception as e:
            self.logger.error(f"Error inserting multiple readings: {e}")

    def insert_event(self, event_type: str, description: str = None, data: str = None):
        """
        Insert system event into database.

        Args:
            event_type: Type of event (e.g., 'startup', 'error', 'warning')
            description: Human-readable description
            data: Additional data (JSON string)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_events (event_type, description, data)
                    VALUES (?, ?, ?)
                ''', (event_type, description, data))

        except Exception as e:
            self.logger.error(f"Error inserting event: {e}")

    def insert_control_action(self, action_type: str, heating_state: bool,
                             pump_state: bool, average_temperature: Optional[float] = None,
                             setpoint: Optional[float] = None):
        """
        Insert control action into database.

        Args:
            action_type: Type of action (e.g., 'heating_on', 'heating_off')
            heating_state: Current heating relay state
            pump_state: Current pump relay state
            average_temperature: Average temperature at time of action
            setpoint: Temperature setpoint at time of action
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO control_actions
                    (action_type, heating_state, pump_state, average_temperature, setpoint)
                    VALUES (?, ?, ?, ?, ?)
                ''', (action_type, heating_state, pump_state, average_temperature, setpoint))

        except Exception as e:
            self.logger.error(f"Error inserting control action: {e}")

    def get_temperature_history(self, hours: int = 24, tank_number: Optional[int] = None) -> List[Dict]:
        """
        Get temperature history for specified time period.

        Args:
            hours: Number of hours to retrieve
            tank_number: Filter by tank number (None for all tanks)

        Returns:
            List of temperature reading dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cutoff_time = self._get_utc_now() - timedelta(hours=hours)

                if tank_number is not None:
                    cursor.execute('''
                        SELECT * FROM temperature_readings
                        WHERE timestamp >= ? AND tank_number = ?
                        ORDER BY timestamp ASC
                    ''', (cutoff_time, tank_number))
                else:
                    cursor.execute('''
                        SELECT * FROM temperature_readings
                        WHERE timestamp >= ?
                        ORDER BY timestamp ASC
                    ''', (cutoff_time,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting temperature history: {e}")
            return []

    def get_average_temperature_history(self, hours: int = 24, interval_minutes: int = 5) -> List[Dict]:
        """
        Get average temperature history aggregated by time interval.

        Args:
            hours: Number of hours to retrieve
            interval_minutes: Grouping interval in minutes

        Returns:
            List of averaged temperature readings with separate tank values
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cutoff_time = self._get_utc_now() - timedelta(hours=hours)

                cursor.execute(f'''
                    SELECT
                        datetime(
                            (strftime('%s', timestamp) / ({interval_minutes} * 60)) * ({interval_minutes} * 60),
                            'unixepoch'
                        ) as timestamp,
                        AVG(CASE WHEN tank_number = 1 THEN temperature END) as tank1,
                        AVG(CASE WHEN tank_number = 2 THEN temperature END) as tank2,
                        AVG(CASE WHEN tank_number = 3 THEN temperature END) as tank3,
                        AVG(temperature) as average
                    FROM temperature_readings
                    WHERE timestamp >= ?
                    GROUP BY timestamp
                    ORDER BY timestamp ASC
                ''', (cutoff_time,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting averaged temperature history: {e}")
            return []

    def get_recent_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict]:
        """
        Get recent system events.

        Args:
            limit: Maximum number of events to retrieve
            event_type: Filter by event type (None for all types)

        Returns:
            List of event dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if event_type:
                    cursor.execute('''
                        SELECT * FROM system_events
                        WHERE event_type = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', (event_type, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM system_events
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', (limit,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting events: {e}")
            return []

    def get_control_history(self, hours: int = 24) -> List[Dict]:
        """
        Get control action history.

        Args:
            hours: Number of hours to retrieve

        Returns:
            List of control action dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cutoff_time = self._get_utc_now() - timedelta(hours=hours)

                cursor.execute('''
                    SELECT * FROM control_actions
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (cutoff_time,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting control history: {e}")
            return []

    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        Remove old data beyond retention period.

        Args:
            days_to_keep: Number of days of data to keep
        """
        try:
            # Delete old data within transaction
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cutoff_time = self._get_utc_now() - timedelta(days=days_to_keep)

                # Clean up old temperature readings
                cursor.execute('''
                    DELETE FROM temperature_readings
                    WHERE timestamp < ?
                ''', (cutoff_time,))
                temp_deleted = cursor.rowcount

                # Clean up old events
                cursor.execute('''
                    DELETE FROM system_events
                    WHERE timestamp < ?
                ''', (cutoff_time,))
                events_deleted = cursor.rowcount

                # Clean up old control actions
                cursor.execute('''
                    DELETE FROM control_actions
                    WHERE timestamp < ?
                ''', (cutoff_time,))
                actions_deleted = cursor.rowcount

                self.logger.info(
                    f"Cleaned up old data: {temp_deleted} temperatures, "
                    f"{events_deleted} events, {actions_deleted} actions"
                )

            # Vacuum database outside transaction to reclaim space
            if temp_deleted > 0 or events_deleted > 0 or actions_deleted > 0:
                conn = sqlite3.connect(self.db_path)
                conn.execute('VACUUM')
                conn.close()
                self.logger.info("Database vacuumed successfully")

        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")

    def get_statistics(self, hours: int = 24) -> Dict:
        """
        Get statistical summary of recent data.

        Args:
            hours: Time period for statistics

        Returns:
            Dictionary with statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cutoff_time = self._get_utc_now() - timedelta(hours=hours)

                # Overall temperature statistics
                cursor.execute('''
                    SELECT
                        COUNT(*) as reading_count,
                        AVG(temperature) as avg_temperature,
                        MIN(temperature) as min_temperature,
                        MAX(temperature) as max_temperature
                    FROM temperature_readings
                    WHERE timestamp >= ?
                ''', (cutoff_time,))

                overall_stats = dict(cursor.fetchone())

                # Per-tank temperature statistics
                cursor.execute('''
                    SELECT
                        tank_number,
                        COUNT(*) as reading_count,
                        AVG(temperature) as avg_temperature,
                        MIN(temperature) as min_temperature,
                        MAX(temperature) as max_temperature
                    FROM temperature_readings
                    WHERE timestamp >= ? AND tank_number IS NOT NULL
                    GROUP BY tank_number
                    ORDER BY tank_number
                ''', (cutoff_time,))

                tanks = [dict(row) for row in cursor.fetchall()]

                # Control statistics - calculate time based on state changes
                cursor.execute('''
                    SELECT
                        action_type,
                        timestamp
                    FROM control_actions
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (cutoff_time,))

                actions = cursor.fetchall()

                # Calculate heating/pump on time
                heating_on_time = 0
                pump_on_time = 0
                heating_cycles = 0

                heating_on = False
                pump_on = False
                last_heating_on_time = None
                last_pump_on_time = None

                for action in actions:
                    action_dict = dict(action)
                    action_type = action_dict['action_type']
                    timestamp = datetime.fromisoformat(action_dict['timestamp'])

                    if action_type == 'heating_on':
                        heating_on = True
                        heating_cycles += 1
                        last_heating_on_time = timestamp
                    elif action_type == 'heating_off' and heating_on:
                        heating_on = False
                        if last_heating_on_time:
                            heating_on_time += (timestamp - last_heating_on_time).total_seconds()

                # If heating is still on, count until now
                if heating_on and last_heating_on_time:
                    heating_on_time += (self._get_utc_now() - last_heating_on_time).total_seconds()

                # Estimate pump time (same as heating time + pump_delay)
                pump_on_time = heating_on_time

                control_stats = {
                    'heating_on_time': heating_on_time,
                    'pump_on_time': pump_on_time,
                    'heating_cycles': heating_cycles
                }

                return {
                    'overall': overall_stats,
                    'tanks': tanks,
                    'control': control_stats,
                    'period_hours': hours
                }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}
