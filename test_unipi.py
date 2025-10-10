#!/usr/bin/env python3
"""
Simple test script to verify Evok API connectivity with Unipi 1.1
"""

import sys
sys.path.insert(0, '/home/jarek/Documents/Projects/beatrice-ttcs-flask')

from evok_client import EvokClient
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    print("=" * 60)
    print("Unipi 1.1 Evok API Test")
    print("=" * 60)
    print()

    # Connect to Unipi
    print("Connecting to Evok API at 192.168.2.234:8080...")
    client = EvokClient(host='192.168.2.234', port=8080)
    print()

    # Test 1: Discover sensors
    print("Test 1: Discovering temperature sensors...")
    sensors = client.get_all_sensors()
    if sensors:
        print(f"✓ Found {len(sensors)} temperature sensor(s):")
        for sensor in sensors:
            print(f"  - Circuit: {sensor['circuit']}")
            print(f"    Type: {sensor.get('type', 'Unknown')}")
            print(f"    Value: {sensor.get('value', 'N/A')}°C")
            print()
    else:
        print("✗ No sensors found!")
        return
    print()

    # Test 2: Read temperature
    if sensors:
        sensor_id = sensors[0]['circuit']
        print(f"Test 2: Reading temperature from sensor {sensor_id}...")
        temp = client.get_temperature(sensor_id)
        if temp is not None:
            print(f"✓ Temperature: {temp:.2f}°C")
        else:
            print("✗ Failed to read temperature")
    print()

    # Test 3: Relay control
    print("Test 3: Testing relay control...")
    print("  Turning relay 1_01 ON...")
    if client.set_relay('1_01', True):
        print("  ✓ Relay 1_01 turned ON")

        import time
        time.sleep(2)

        print("  Turning relay 1_01 OFF...")
        if client.set_relay('1_01', False):
            print("  ✓ Relay 1_01 turned OFF")
        else:
            print("  ✗ Failed to turn relay OFF")
    else:
        print("  ✗ Failed to turn relay ON")
    print()

    # Test 4: Check relay state
    print("Test 4: Checking relay state...")
    state = client.get_relay_state('1_01')
    if state is not None:
        print(f"✓ Relay 1_01 state: {'ON' if state else 'OFF'}")
    else:
        print("✗ Failed to get relay state")
    print()

    print("=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == '__main__':
    main()
