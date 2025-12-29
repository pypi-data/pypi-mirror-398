# Mudra SDK Python

Python SDK for Mudra with native library support. This SDK enables you to connect to and interact with Mudra devices via Bluetooth Low Energy (BLE).

## Features

- 🔌 **Bluetooth Low Energy (BLE) Support** - Connect to Mudra devices wirelessly
- 📱 **Cross-Platform** - Supports Windows, macOS
- 🎯 **Device Discovery** - Scan and discover nearby Mudra devices
- 📊 **Pressure Sensing** - Real-time pressure data from the device
- 🔄 **Event-Driven Architecture** - Use delegates for handling device events

## Requirements

- Python 3.7 or higher
- Bluetooth-enabled computer
- Mudra device

## Installation

```bash
pip install mudra-sdk
```

## Quick Start

### Basic Setup

```python
import asyncio
from mudra_sdk import Mudra, MudraDevice
from mudra_sdk.models.callbacks import MudraDelegate

# Create Mudra instance
mudra = Mudra()

# Implement delegate to handle device events
class MyMudraDelegate(MudraDelegate):
    def on_device_discovered(self, device: MudraDevice):
        print(f"Discovered: {device.name} ({device.address})")

    def on_mudra_device_connected(self, device: MudraDevice):
        print(f"Device connected: {device.name}")

    def on_mudra_device_disconnected(self, device: MudraDevice):
        print(f"Device disconnected: {device.name}")

    def on_mudra_device_connecting(self, device: MudraDevice):
        print(f"Device connecting: {device.name}...")

    def on_mudra_device_disconnecting(self, device: MudraDevice):
        print(f"Device disconnecting: {device.name}...")

    def on_mudra_device_connection_failed(self, device: MudraDevice, error: str):
        print(f"Connection failed: {device.name}, Error: {error}")

    def on_bluetooth_state_changed(self, state: bool):
        print(f"Bluetooth state changed: {'On' if state else 'Off'}")

# Set the delegate
mudra.set_delegate(MyMudraDelegate())
```

### Scanning for Devices

```python
async def main():
    mudra = Mudra()
    mudra.set_delegate(MyMudraDelegate())
    
    # Start scanning for Mudra devices
    await mudra.scan()
    
    # Wait for devices to be discovered
    await asyncio.sleep(10)
    
    # Stop scanning when done
    await mudra.stop_scan()

# Run the async function
asyncio.run(main())
```

### Connecting to a Device

```python
# Store discovered devices
discovered_devices = []

class MyMudraDelegate(MudraDelegate):
    def on_device_discovered(self, device: MudraDevice):
        discovered_devices.append(device)
        print(f"Discovered: {device.name}")

async def main():
    mudra = Mudra()
    mudra.set_delegate(MyMudraDelegate())
    
    # Start scanning
    await mudra.scan()
    await asyncio.sleep(5)  # Wait for discovery
    
    # Connect to the first discovered device
    if discovered_devices:
        device = discovered_devices[0]
        await device.connect()
        print(f"Connected to {device.name}")
        
        # ... use the device ...
        
        # Disconnect when done
        await device.disconnect()

asyncio.run(main())
```

## Usage Examples

### Pressure Data

Enable pressure sensing to receive real-time pressure data from the device:

```python
def on_pressure_ready(pressure_data: int):
    print(f"Pressure: {pressure_data}")

async def main():
    # ... connect to device ...
    
    # Enable pressure sensing
    await mudraDevice.set_on_pressure_ready(on_pressure_ready)
    
    # ... use device ...
    
    # Disable pressure sensing
    await mudraDevice.set_on_pressure_ready(None)

asyncio.run(main())
```

## Platform Support

The SDK includes native libraries for the following platforms:

- **Windows**
- **macOS**

The appropriate library is automatically loaded based on your platform.

## API Reference

### Mudra Class

Main entry point for the SDK.

- `scan()` - Start scanning for Mudra devices
- `stop_scan()` - Stop scanning for devices
- `set_delegate(delegate: MudraDelegate)` - Set the delegate for handling device events
- `connect(device: MudraDevice)` - Connect to a device
- `disconnect(device: MudraDevice)` - Disconnect from a device

### MudraDevice Class

Represents a discovered or connected Mudra device.

- `connect()` - Connect to the device (async)
- `disconnect()` - Disconnect from the device (async)
- `set_on_pressure_ready(callback)` - Enable/disable pressure sensing (async)

### MudraDelegate Interface

Implement this interface to handle device events:

- `on_device_discovered(device: MudraDevice)` - Called when a device is discovered
- `on_mudra_device_connected(device: MudraDevice)` - Called when a device connects
- `on_mudra_device_disconnected(device: MudraDevice)` - Called when a device disconnects
- `on_mudra_device_connecting(device: MudraDevice)` - Called when a device is connecting
- `on_mudra_device_disconnecting(device: MudraDevice)` - Called when a device is disconnecting
- `on_mudra_device_connection_failed(device: MudraDevice, error: str)` - Called when connection fails
- `on_bluetooth_state_changed(state: bool)` - Called when Bluetooth state changes

## Complete Example

Here's a complete example that demonstrates the full workflow:

```python
import asyncio
from mudra_sdk import Mudra, MudraDevice
from mudra_sdk.models.callbacks import MudraDelegate

discovered_devices = []
connected_device = None

class MyMudraDelegate(MudraDelegate):
    def on_device_discovered(self, device: MudraDevice):
        print(f"✓ Discovered: {device.name} ({device.address})")
        discovered_devices.append(device)

    def on_mudra_device_connected(self, device: MudraDevice):
        global connected_device
        connected_device = device
        print(f"✓ Connected to: {device.name}")

    def on_mudra_device_disconnected(self, device: MudraDevice):
        print(f"✓ Disconnected from: {device.name}")

    def on_mudra_device_connecting(self, device: MudraDevice):
        print(f"→ Connecting to: {device.name}...")

    def on_mudra_device_disconnecting(self, device: MudraDevice):
        print(f"→ Disconnecting from: {device.name}...")

    def on_mudra_device_connection_failed(self, device: MudraDevice, error: str):
        print(f"✗ Connection failed: {device.name}, Error: {error}")

    def on_bluetooth_state_changed(self, state: bool):
        print(f"Bluetooth: {'On' if state else 'Off'}")

def on_pressure_ready(pressure_data: int):
    print(f"Pressure: {pressure_data}")
    

async def main():
    mudra = Mudra()
    mudra.set_delegate(MyMudraDelegate())
    
    print("Scanning for Mudra devices...")
    await mudra.scan()
    
    # Wait for devices to be discovered
    await asyncio.sleep(5)
    
    if discovered_devices:
        device = discovered_devices[0]
        print(f"\nConnecting to {device.name}...")
        await device.connect()
        
        # Enable all features
        await device.set_on_pressure_ready(on_pressure_ready)
        
        print("\nDevice ready! Interacting with device for 30 seconds...")
        await asyncio.sleep(30)
        
        # Cleanup
        await device.set_on_pressure_ready(None)
        await device.disconnect()
    else:
        print("No devices found.")
    
    await mudra.stop_scan()

if __name__ == "__main__":
    asyncio.run(main())
```

## Documentation

For more detailed documentation, visit: [https://wearable-devices.github.io/#welcome](https://wearable-devices.github.io/#welcome)

## Support
For issues, questions, or contributions please contact [foad.k@wearabldevices.co.il](mailto:foad.k@wearabldevices.co.il)
