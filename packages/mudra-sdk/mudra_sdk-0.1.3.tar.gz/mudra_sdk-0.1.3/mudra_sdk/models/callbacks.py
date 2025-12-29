from abc import ABC, abstractmethod

from bleak.backends.device import BLEDevice

from mudra_sdk.models.enums import AirTouchButton, GestureType
from ..service.ble_service import MudraCharacteristicUUID
import mudra_sdk.models.mudra_device as mudraDeviceModule

from typing import Callable

OnBleDeviceDiscovered = Callable[[mudraDeviceModule.MudraDevice], None]  
OnBleDeviceConnected = Callable[[mudraDeviceModule.MudraDevice], None]
OnBleDeviceDisconnected = Callable[[mudraDeviceModule.MudraDevice], None]
OnBleDeviceDisconnecting = Callable[[mudraDeviceModule.MudraDevice], None]
OnBleDeviceConnecting = Callable[[mudraDeviceModule.MudraDevice], None]
OnBleDeviceConnectionFailed = Callable[[mudraDeviceModule.MudraDevice, str], None]
OnBluetoothStateChanged = Callable[[bool], None]

class MudraDelegate(ABC):
    @abstractmethod
    def on_device_discovered(self, device: mudraDeviceModule.MudraDevice):
        pass

    @abstractmethod
    def on_mudra_device_disconnected(self, device: mudraDeviceModule.MudraDevice):
        pass

    @abstractmethod
    def on_mudra_device_disconnecting(self, device: mudraDeviceModule.MudraDevice):
        pass

    @abstractmethod
    def on_mudra_device_connected(self, device: mudraDeviceModule.MudraDevice):
        pass

    @abstractmethod
    def on_mudra_device_connecting(self, device: mudraDeviceModule.MudraDevice):
        pass

    @abstractmethod
    def on_mudra_device_connection_failed(self, device: mudraDeviceModule.MudraDevice, error: str):
        pass

    @abstractmethod
    def on_bluetooth_state_changed(self, state: bool):
        pass



# --- Implementation of BleServiceDelegate abstract methods ---
class BleServiceDelegate(ABC):
    @abstractmethod
    def on_device_discovered(self, device: BLEDevice):
        pass

    @abstractmethod
    def on_mudra_device_disconnected(self, device: BLEDevice):
        pass

    @abstractmethod
    def on_mudra_device_disconnecting(self, device: BLEDevice):
        pass

    @abstractmethod
    def on_mudra_device_connected(self, device: BLEDevice):
        pass

    @abstractmethod
    def on_mudra_device_connecting(self, device: BLEDevice):
        pass

    @abstractmethod
    def on_mudra_device_connection_failed(self, device: BLEDevice, error: str):
        pass

    @abstractmethod
    def on_bluetooth_state_changed(self, state: bool):
        pass

    @abstractmethod
    def on_ble_characteristic_discovered(self, device: BLEDevice, characteristic_uuid: MudraCharacteristicUUID):
        pass

    @abstractmethod
    def on_pressure_data_received(self, device_address: str, pressure_data: int):
        pass
    
    @abstractmethod
    def on_gesture_data_received(self, device_address: str, gesture_type: GestureType):
        pass

    @abstractmethod
    def on_air_touch_button_changed_received(self, device_address: str, air_touch_button: AirTouchButton):
        pass

    @abstractmethod
    def on_firmware_status_updated(self, device_address: str, data: bytes):
        pass

    @abstractmethod
    def handle_snc(self, device_address: str, data: bytes):
        pass

    @abstractmethod
    def handle_imu(self, device_address: str, data: bytes):
        pass

    @abstractmethod
    def on_navigation_delta_received(self, device_address: str, delta_x: int, delta_y: int):
        pass