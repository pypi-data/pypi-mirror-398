import asyncio
from calendar import c
from enum import Enum
from typing import Any, Callable, Optional, Dict
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.service import BleakGATTServiceCollection

from mudra_sdk.models.enums import AirTouchButton, FirmwareCallbacks, GestureType, MudraBLEServicesUUID, MudraCharacteristicUUID

from ..models.callbacks import BleServiceDelegate

from typing import Optional

class BleService:
    _instance = None
    _delegate: Optional[BleServiceDelegate] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, delegate: BleServiceDelegate):
        if not hasattr(self, '_initialized'):
            self._discovered_devices: set[Any] = set()
            self._scan_task = None
            self._scanner: Optional[BleakScanner] = None
            self._delegate = delegate
            self._connected_clients: Dict[str, BleakClient] = {}  # address -> client
            self._initialized = True

    ### ----------------------- Connection Methods ----------------------- ###
    
    async def connect(self, device: BLEDevice):
        print(f"Connecting to device: {device.name}")
        address = device.address
        
        # Check if already connected
        if address in self._connected_clients:
            print(f"Device {address} is already connected")
            return
        
        try:
            # Notify connecting
            if self._delegate:
                self._delegate.on_mudra_device_connecting(device)
            
            # Create client with disconnect callback.
            client = BleakClient(device, disconnected_callback=lambda client: self._on_disconnect_callback(device))
            
            # Attempt connection
            print(f"Calling BleakClient.connect() for {address}")
            await client.connect()
            import asyncio
            await asyncio.sleep(10)
            
            # Store the connected client
            self._connected_clients[address] = client
            device.client = client 
            
            # Discover services
            print(f"Discovering services for {device.name}")
            services = client.services
            
            # Notify connected
            if self._delegate:
                self._delegate.on_mudra_device_connected(device)
            
            if not await self.init_ble_services(device, services):
                print(f"Failed to initialize BLE services for {device.name} ({address})")
                await self.disconnect(device)
                if self._delegate:
                    self._delegate.on_mudra_device_connection_failed(device, "Failed to initialize BLE services")
                return 
            
            # Optionally store services in the device object
            device.services = services

            print(f"Successfully connected to {device.name} ({address})")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to connect to {address}: {error_msg}")
            
            # Notify connection failed
            if self._delegate:
                self._delegate.on_mudra_device_connection_failed(device, error_msg)
            
            # Clean up if connection attempt failed
            if address in self._connected_clients:
                del self._connected_clients[address]

    async def init_ble_services(self, device: BLEDevice, services: BleakGATTServiceCollection):
        client = device.client  # Get the BleakClient from the device
        
        for service in services:
            service_enum = MudraBLEServicesUUID.from_value(service.uuid)
            if service_enum:
                print(f"  -> Recognized as: {service_enum.name}")
            
            for char in service.characteristics:
                char_enum = MudraCharacteristicUUID.from_value(char.uuid)
                print(f"    Properties: {char.properties}")
                
                # Check if characteristic supports notify or indicate
                can_notify = "notify" in char.properties
                can_indicate = "indicate" in char.properties
                
                if char_enum:
                    if self._delegate:
                        self._delegate.on_ble_characteristic_discovered(device, char_enum)

                try:
                    match char_enum:
                        case MudraCharacteristicUUID.SNC_CHARACTERISTIC:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for SNC characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._snc_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.IMU_CHARACTERISTIC:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for IMU characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._imu_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.COMMAND_CHARACTERISTIC:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for COMMAND characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._command_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.LOGGING_CHARACTERISTIC:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for LOGGING characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._logging_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.MESSAGE_CHARACTERISTIC:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for MESSAGE characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._message_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.BATTERY_CHARACTERISTIC:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for BATTERY characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._battery_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.FIRMWARE_CHARACTERISTIC:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for FIRMWARE characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._firmware_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.SERIAL_RIGHT_PART_CHARACTERISTIC:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for SERIAL RIGHT PART characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._serial_right_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.SERIAL_LEFT_PART_CHARACTERISTIC:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for SERIAL LEFT PART characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._serial_left_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.DFU_WITHOUT_BONDS:
                            if can_indicate:  # DFU typically uses indications
                                print(f"Subscribing to indications for DFU WITHOUT BONDS characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._dfu_notification_handler(device, sender, data))
                        
                        case MudraCharacteristicUUID.CHARGING_STATE:
                            if can_notify or can_indicate:
                                print(f"Subscribing to notifications for CHARGING STATE characteristic: {char.uuid}")
                                await client.start_notify(char.uuid, lambda sender, data: self._charging_notification_handler(device, sender, data))
                        case _:
                            if char_enum:
                                print(f"No notification handler for: {char_enum.name}")
                            else:
                                print(f"Unrecognized characteristic: {char.uuid}")
                                
                except Exception as e:
                    print(f"Failed to subscribe to {char.uuid}: {e}")
                    return False
        return True

    # Notification handler examples
    def _snc_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle SNC characteristic notifications."""
        if self._delegate:
            self._delegate.handle_snc(device.address, data)

    def _imu_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle IMU characteristic notifications."""
        if self._delegate:
            self._delegate.handle_imu(device.address, data)

    def _command_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle COMMAND characteristic notifications."""
        address = device.address
        firmware_callback = FirmwareCallbacks.from_data(data)
        if firmware_callback != FirmwareCallbacks.BAND_CONNECTION_STATUS:
            print(f"COMMAND notification from {sender} (device {address}): {data.hex()}")
        match firmware_callback:
            case FirmwareCallbacks.STOP_ADVERTISING:
                print("STOP_ADVERTISING")
            case FirmwareCallbacks.FIRMWARE_CRASH:
                print("FIRMWARE_CRASH")
            case FirmwareCallbacks.RESET_FUEL_GAUGE:
                print("RESET_FUEL_GAUGE")
            case FirmwareCallbacks.GESUTURE_RELEASE:
                print("GESUTURE_RELEASE")
                if self._delegate:
                    self._delegate.on_air_touch_button_changed_received(device.address, AirTouchButton.release)
            case FirmwareCallbacks.FIRMWARE_STATUS:
                if self._delegate:
                    self._delegate.on_firmware_status_updated(device.address, data)
            case FirmwareCallbacks.NAVIGATION_DELTA:
                delta_x = self._convert_two_bytes_to_navigation_delta(data[2], data[1])
                delta_y = self._convert_two_bytes_to_navigation_delta(data[4], data[3])
                if self._delegate:
                    self._delegate.on_navigation_delta_received(device.address, delta_x, delta_y)
            case FirmwareCallbacks.NAVIGATION_DIRECTION:
                print("NAVIGATION_DIRECTION")
            case FirmwareCallbacks.PRESSURE:
                if self._delegate:
                    self._delegate.on_pressure_data_received(device.address, data[1])
            case FirmwareCallbacks.GESTURE_TAP:
                if self._delegate:
                    self._delegate.on_gesture_data_received(device.address, GestureType.TAP)
                    self._delegate.on_air_touch_button_changed_received(device.address, AirTouchButton.press)
            case FirmwareCallbacks.GESTURE_DOUBLE_TAP:
                if self._delegate:
                    self._delegate.on_gesture_data_received(device.address, GestureType.DOUBLE_TAP)
            case FirmwareCallbacks.GESTURE_TWIST:
                if self._delegate:
                    self._delegate.on_gesture_data_received(device.address, GestureType.TWIST)
            case FirmwareCallbacks.GESTURE_DOUBLE_TWIST:
                if self._delegate:
                    self._delegate.on_gesture_data_received(device.address, GestureType.DOUBLE_TWIST)
            case FirmwareCallbacks.MAPPER_UPDATED:
                print("MAPPER_UPDATED")
            case FirmwareCallbacks.SAMPLE_TYPE_CHANGED:
                print("SAMPLE_TYPE_CHANGED")
            case FirmwareCallbacks.BAND_CONNECTION_STATUS:
                pass
            case FirmwareCallbacks.NONE:
                print("NONE")
            case _:
                print("Unknown firmware callback")

    def _logging_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle LOGGING characteristic notifications."""
        print(f"LOGGING notification from {sender} (device {device.address}): {data.hex()}")

    def _message_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle MESSAGE characteristic notifications."""
        print(f"MESSAGE notification from {sender} (device {device.address}): {data.hex()}")

    def _battery_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle BATTERY characteristic notifications."""
        battery_level = int(data[0]) if len(data) > 0 else 0
        print(f"BATTERY notification from {sender} (device {device.address}): {battery_level}%")

    def _firmware_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle FIRMWARE characteristic notifications."""
        print(f"FIRMWARE notification from {sender} (device {device.address}): {data.hex()}")

    def _serial_right_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle SERIAL RIGHT PART characteristic notifications."""
        print(f"SERIAL RIGHT notification from {sender} (device {device.address}): {data.hex()}")

    def _serial_left_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle SERIAL LEFT PART characteristic notifications."""
        print(f"SERIAL LEFT notification from {sender} (device {device.address}): {data.hex()}")

    def _dfu_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle DFU WITHOUT BONDS characteristic notifications/indications."""
        print(f"DFU notification from {sender} (device {device.address}): {data.hex()}")

    def _charging_notification_handler(self, device: BLEDevice, sender: int, data: bytearray):
        """Handle CHARGING STATE characteristic notifications."""
        is_charging = bool(data[0]) if len(data) > 0 else False
        print(f"CHARGING STATE notification from {sender} (device {device.address}): {'Charging' if is_charging else 'Not charging'}")


    def _convert_two_bytes_to_navigation_delta(self, byte1: int, byte2: int) -> int:
        """Convert two bytes (high, low) into a signed 16-bit navigation delta."""
        value = (byte1 << 8) | byte2
        if value & 0x8000:
            value = value - 0x10000  # Convert to negative for signed 16-bit
        return value
    
    async def disconnect(self, device: BLEDevice):
        address = device.address
        
        # Check if device is connected
        if address not in self._connected_clients:
            print(f"Device {address} is not connected")
            return
        
        try:
            # Notify disconnecting
            if self._delegate:
                self._delegate.on_mudra_device_disconnecting(device)
            
            client = self._connected_clients[address]

            # If it's already disconnected (e.g. due to unexpected disconnect),
            # skip calling disconnect() to avoid spurious errors.
            if getattr(client, "is_connected", False):
                # Disconnect
                await client.disconnect()
            
            # Remove from connected clients
            del self._connected_clients[address]
            device.client = None  # Clear client reference if stored
            
            # Notify disconnected
            if self._delegate:
                self._delegate.on_mudra_device_disconnected(device)
            
            print(f"Successfully disconnected from {device.name} ({address})")
            
        except Exception as e:
            if address in self._connected_clients:
                del self._connected_clients[address]
            device.client = None

    def _on_disconnect_callback(self, device: BLEDevice):
        """Internal callback triggered when device disconnects unexpectedly."""
        address = device.address
        
        print(f"Device {address} disconnected unexpectedly")
        
        # Clean up
        if address in self._connected_clients:
            del self._connected_clients[address]
            device.client = None
        
        # Notify delegate
        if self._delegate:
            self._delegate.on_mudra_device_disconnected(device)

    def is_connected(self, device: BLEDevice) -> bool:
        """Check if a device is currently connected."""
        address = device.address
        if address not in self._connected_clients:
            return False
        
        client = self._connected_clients[address]
        return client.is_connected

    async def disconnect_all(self):
        """Disconnect all connected devices."""
        devices_to_disconnect = list(self._connected_clients.keys())
        
        for address in devices_to_disconnect:
            client = self._connected_clients[address]
            try:
                await client.disconnect()
            except Exception as e:
                print(f"Error disconnecting {address}: {e}")
            finally:
                if address in self._connected_clients:
                    del self._connected_clients[address]


    async def send_general_command(self, device: BLEDevice, command: bytes):
        try:
            client = device.client
            if client:
                await client.write_gatt_char(MudraCharacteristicUUID.COMMAND_CHARACTERISTIC.value, command)
            else:
                print(f"Device {device.address} is not connected")
        except Exception as e:
            print(f"Error sending generic command to {device.address}: {e}")


    ### ----------------------- Scan Methods ----------------------- ###
    
    @property
    def _is_scanning(self) -> bool:
        """Check if currently scanning for devices."""
        return self._scan_task is not None and not self._scan_task.done()

    async def scan(self):
        """Start scanning for BLE devices."""
        if self._is_scanning:
            return
        print("Starting scan")
        self._discovered_devices.clear()
        self._scan_task = asyncio.create_task(self._scan_loop())

    async def stop_scanning(self):
        """Stop scanning for BLE devices."""
        if not self._is_scanning:
            return
        print("Stopping scan")
        
        # Cancel the scan task
        if self._scan_task and not self._scan_task.done():
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
        
        # Stop the scanner if it exists
        if self._scanner:
            try:
                await self._scanner.stop()
            except Exception:
                pass
            finally:
                self._scanner = None
        
        self._scan_task = None

    async def _scan_loop(self):
        """Internal method that performs the actual scanning."""
        try:
            self._scanner = BleakScanner(detection_callback=self._on_device_detected)
            
            await self._scanner.start()
            print("Scan started successfully")
            
            # Keep scanning until cancelled
            while True:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            print("Scan cancelled")
            if self._scanner:
                try:
                    await self._scanner.stop()
                except Exception:
                    pass
            raise
        except Exception as e:
            print(f"Error during scan: {e}")
            raise
        finally:
            self._scanner = None
            self._scan_task = None

    def _on_device_detected(self, device: BLEDevice, advertisement_data):
        """Internal callback when a BLE device is detected."""            
        if self._delegate:
            try:
                if device.name and "Mudra" in device.name:
                    # Use address as identifier, since address is unique per BLE device
                    if device.address not in self._discovered_devices:
                        self._discovered_devices.add(device.address)
                        self._delegate.on_device_discovered(device)
            except Exception as e:
                print(f"Error processing device {device.address}: {e}")