#!/usr/bin/env python3
"""
Test script for database cleanup functionality.

This script tests the cleanup_old_data function by:
1. Checking current database size and row counts
2. Running the cleanup function
3. Verifying cleanup results
"""

import os
import sys
from datetime import datetime, timedelta
from database import Database

def get_file_size(filepath):
    """Get file size in MB."""
    if os.path.exists(filepath):
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)  # Convert to MB
    return 0

def get_row_counts(db):
    """Get row counts for all tables."""
    with db._get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM temperature_readings")
        temp_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM system_events")
        events_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM control_actions")
        actions_count = cursor.fetchone()[0]

        return temp_count, events_count, actions_count

def get_date_range(db):
    """Get oldest and newest timestamps in database."""
    with db._get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM temperature_readings")
        result = cursor.fetchone()

        if result[0]:
            return result[0], result[1]
        return None, None

def main():
    print("=" * 60)
    print("Database Cleanup Test")
    print("=" * 60)

    db_path = 'data.db'

    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found!")
        print("Run the application first to create the database.")
        return 1

    # Initialize database
    db = Database(db_path)

    # Get initial state
    print("\n--- BEFORE CLEANUP ---")
    size_before = get_file_size(db_path)
    print(f"Database file size: {size_before:.2f} MB")

    temp_count, events_count, actions_count = get_row_counts(db)
    print(f"Temperature readings: {temp_count:,}")
    print(f"System events: {events_count:,}")
    print(f"Control actions: {actions_count:,}")
    print(f"Total rows: {temp_count + events_count + actions_count:,}")

    oldest, newest = get_date_range(db)
    if oldest:
        print(f"\nDate range:")
        print(f"  Oldest: {oldest}")
        print(f"  Newest: {newest}")

    # Test cleanup with different retention periods
    print("\n--- RUNNING CLEANUP TEST ---")

    # Ask user for retention period
    print("\nEnter retention period in days (default: 365):")
    print("  0 = Delete all data")
    print("  7 = Keep last week")
    print("  30 = Keep last month")
    print("  365 = Keep last year")

    try:
        retention_input = input("Days to keep: ").strip()
        if retention_input:
            retention_days = int(retention_input)
        else:
            retention_days = 365
    except ValueError:
        print("Invalid input, using default (365 days)")
        retention_days = 365

    print(f"\nRunning cleanup (keeping last {retention_days} days)...")

    try:
        db.cleanup_old_data(days_to_keep=retention_days)
        print("Cleanup completed successfully!")
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 1

    # Get final state
    print("\n--- AFTER CLEANUP ---")
    size_after = get_file_size(db_path)
    print(f"Database file size: {size_after:.2f} MB")

    temp_count_after, events_count_after, actions_count_after = get_row_counts(db)
    print(f"Temperature readings: {temp_count_after:,}")
    print(f"System events: {events_count_after:,}")
    print(f"Control actions: {actions_count_after:,}")
    print(f"Total rows: {temp_count_after + events_count_after + actions_count_after:,}")

    oldest_after, newest_after = get_date_range(db)
    if oldest_after:
        print(f"\nDate range:")
        print(f"  Oldest: {oldest_after}")
        print(f"  Newest: {newest_after}")

    # Calculate differences
    print("\n--- CLEANUP RESULTS ---")
    temp_deleted = temp_count - temp_count_after
    events_deleted = events_count - events_count_after
    actions_deleted = actions_count - actions_count_after
    total_deleted = temp_deleted + events_deleted + actions_deleted
    size_freed = size_before - size_after

    print(f"Rows deleted:")
    print(f"  Temperature readings: {temp_deleted:,}")
    print(f"  System events: {events_deleted:,}")
    print(f"  Control actions: {actions_deleted:,}")
    print(f"  Total: {total_deleted:,}")
    print(f"\nDisk space freed: {size_freed:.2f} MB ({(size_freed/size_before*100) if size_before > 0 else 0:.1f}%)")

    if total_deleted == 0:
        print("\nNote: No data was old enough to be deleted.")
        print(f"All data is within the {retention_days}-day retention period.")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
