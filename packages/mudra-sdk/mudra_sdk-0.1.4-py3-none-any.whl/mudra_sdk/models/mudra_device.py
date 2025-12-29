import asyncio
from typing import Callable, Optional
from bleak.backends.device import BLEDevice

from mudra_sdk.models.enums import AirTouchButton, FirmwareCommand, FirmwareDataType, GestureType, ModelType
from mudra_sdk.models.firmware_status import FirmwareStatus
import mudra_sdk.models.mudra as mudraModule
import mudra_sdk.models.computation_wrapper as computationWrapperModule
from mudra_sdk.service.ble_service import MudraBLEServicesUUID, MudraCharacteristicUUID

class MudraDevice(BLEDevice):
    def __init__(self, ble_device: BLEDevice):
        super().__init__(ble_device.address, ble_device.name, ble_device.details)

        # Initialize characteristic status
        self._characteristic_status = {
            MudraCharacteristicUUID.SNC_CHARACTERISTIC: False,
            MudraCharacteristicUUID.IMU_CHARACTERISTIC: False,
            MudraCharacteristicUUID.COMMAND_CHARACTERISTIC: False,
            MudraCharacteristicUUID.LOGGING_CHARACTERISTIC: False,
            MudraCharacteristicUUID.MESSAGE_CHARACTERISTIC: False,
            MudraCharacteristicUUID.BATTERY_CHARACTERISTIC: False,
            MudraCharacteristicUUID.FIRMWARE_CHARACTERISTIC: False,
            MudraCharacteristicUUID.SERIAL_RIGHT_PART_CHARACTERISTIC: False,
            MudraCharacteristicUUID.SERIAL_LEFT_PART_CHARACTERISTIC: False,
            MudraCharacteristicUUID.DFU_WITHOUT_BONDS: False,
            MudraCharacteristicUUID.CHARGING_STATE: False,
        }

        # Initialize service status
        self._service_status = {
            MudraBLEServicesUUID.COMMAND_SERVICE: False,
            MudraBLEServicesUUID.BATTERY_SERVICE: False,
            MudraBLEServicesUUID.DFU_SERVICE: False,
            MudraBLEServicesUUID.INFORMATION_SERVICE: False,
        }

        self._state_enabled = {
            FirmwareDataType.snc: False,
            FirmwareDataType.imuQuaternion: False,
            FirmwareDataType.imuGyro: False,
            FirmwareDataType.imuAccelometer: False,
            FirmwareDataType.navigation: False,
            FirmwareDataType.embeddedGesture: False,
            FirmwareDataType.embeddedPressure: False,
            FirmwareDataType.embeddedAirTouch: False,
        }

        self._on_pressure_ready: Optional[computationWrapperModule.OnPressureCallback] = None
        self._on_gesture_data_received: Optional[computationWrapperModule.OnGestureDataReceivedCallback] = None
        self._on_air_touch_button_changed_received: Optional[computationWrapperModule.OnAirTouchButtonChangedReceivedCallback] = None
        self._on_navigation_delta_received: Optional[computationWrapperModule.OnNavigationDeltaReceivedCallback] = None

        self._on_snc_ready: Optional[computationWrapperModule.OnRawDataCallback] = None

        self._firmware_status = FirmwareStatus()
        self._computation_wrapper = computationWrapperModule.ComputationWrapper(0, "./models/model.tflite", "./models/model.tflite")
        self._computation_wrapper.set_model_type(ModelType.embedded)
        

    async def connect(self):
        await mudraModule.Mudra().connect(self)

    async def disconnect(self):
        await mudraModule.Mudra().disconnect(self)

    async def send_general_command(self, command: bytes):
        await mudraModule.Mudra().send_general_command(self, command)

    ### ----------------------- Setter Methods ----------------------- ###
    def set_on_gesture_data_received(self, on_gesture_data_received: computationWrapperModule.OnGestureDataReceivedCallback):
        self._on_gesture_data_received = on_gesture_data_received

    def set_on_air_touch_button_changed_received(self, on_air_touch_button_changed_received: computationWrapperModule.OnAirTouchButtonChangedReceivedCallback):
        self._on_air_touch_button_changed_received = on_air_touch_button_changed_received

    def set_on_navigation_delta_received(self, on_navigation_delta_received: computationWrapperModule.OnNavigationDeltaReceivedCallback):
        print(f"Mudra device : Setting on navigation delta received callback ")
        self._on_navigation_delta_received = on_navigation_delta_received
    ### ----------------------- Delegate Methods ----------------------- ###

    def on_characteristic_discovered(self, characteristic_uuid: MudraCharacteristicUUID):
        print(f"Characteristic discovered: {characteristic_uuid}")
        self._characteristic_status[characteristic_uuid] = True

    def on_pressure_data_received(self, pressure_data: int):
        if self._on_pressure_ready:
            self._on_pressure_ready(pressure_data)

    def on_gesture_data_received(self, gesture_type: GestureType):
        if self._on_gesture_data_received:
            self._on_gesture_data_received(gesture_type)

    def on_air_touch_button_changed_received(self, air_touch_button: AirTouchButton):
        if self._on_air_touch_button_changed_received:
            self._on_air_touch_button_changed_received(air_touch_button)

    def on_firmware_status_updated(self, data: bytes):
        self._firmware_status.update(data)

    def _handle_data(self, data: bytes, error_message: str, native_handler_attr: str):
        try:
            self._computation_wrapper.handle_data(data, len(data))
        except Exception as e:
            print(f"Exception in _handle_data: {e}")

    def handle_snc(self, data: bytes):
        self._handle_data(data, "Failed to handle SNC. The handleSnc function is not available.", "handleSnc")

    def handle_imu(self, data: bytes):
        self._handle_data(data, "Failed to handle IMU. The handleImu function is not available.", "handleImu")


    def on_navigation_delta_received(self, delta_x: int, delta_y: int):
        if self._on_navigation_delta_received:
            self._on_navigation_delta_received(delta_x, delta_y)


    # async def set_on_snc_ready(self, callback: computationWrapperModule.OnRawDataCallback) -> None:
    #     self._on_snc_ready = callback
    #     self._computation_wrapper.set_on_snc_ready(callback)
    #     await self._update_state_enabled()
    
    # async def set_on_imu_acc_ready(self, callback: computationWrapperModule.OnRawDataCallback) -> None:
    #     self._on_imu_acc_ready = callback
    #     self._computation_wrapper.set_on_imu_acc_ready(callback)
    #     await self._update_state_enabled()
    
    # async def set_on_imu_gyro_ready(self, callback: computationWrapperModule.OnRawDataCallback) -> None:
    #     self._on_imu_gyro_ready = callback
    #     self._computation_wrapper.set_on_imu_gyro_ready(callback)
    #     await self._update_state_enabled()

    async def set_on_pressure_ready(self, callback: computationWrapperModule.OnPressureCallback) -> None:
        self._on_pressure_ready = callback
        self._computation_wrapper.set_on_pressure_ready(callback)
        await self._update_state_enabled()

    ### ----------------------- Is Data Needed ----------------------- ###
    
    async def _update_state_enabled(self):
        print("Updating state enabled for all firmware data types")
        for firmware_data_type in FirmwareDataType:
            await self._update_data_enabled(firmware_data_type)

    async def _update_data_enabled(self, firmware_data_type):

        is_needed = self._computation_wrapper.is_data_needed(firmware_data_type.value)
        print(f"Is data needed for {firmware_data_type.name} is {is_needed}")
        if is_needed != self._state_enabled.get(firmware_data_type):
            print(f"Updating state enabled for {firmware_data_type.name} to {is_needed}")
            self._state_enabled[firmware_data_type] = is_needed
            print(f"State enabled for {firmware_data_type.name} is {self._state_enabled.get(firmware_data_type)}")
            await self._update_configuration(firmware_data_type)


    async def get_firmware_command(self, command: int) -> bytes:
        return mudraModule.Mudra().get_firmware_command(command)

    async def _update_configuration(self, firmware_data_type):
        print(f"Updating configuration for {firmware_data_type.name}")
        if self._characteristic_status[MudraCharacteristicUUID.COMMAND_CHARACTERISTIC]:
            cmd: Optional[bytes] = None
            if firmware_data_type == FirmwareDataType.snc:
                print(f"Updating SNC configuration")
                cmd = FirmwareCommand.enableSnc.id if self._state_enabled.get(firmware_data_type) else FirmwareCommand.disableSnc.id
            elif firmware_data_type == FirmwareDataType.embeddedPressure:
                print(f"Updating Pressure configuration")
                cmd = FirmwareCommand.enablePressure.id if self._state_enabled.get(firmware_data_type) else FirmwareCommand.disablePressure.id
            elif firmware_data_type == FirmwareDataType.imuAccelometer:
                print(f"Updating IMU Acc configuration")
                cmd = FirmwareCommand.enableImuAccRaw.id if self._state_enabled.get(firmware_data_type) else FirmwareCommand.disableImuAccRaw.id
            elif firmware_data_type == FirmwareDataType.imuGyro:
                print(f"Updating IMU Gyro configuration")
                cmd = FirmwareCommand.enableImuGyro.id if self._state_enabled.get(firmware_data_type) else FirmwareCommand.disableImuGyro.id
            elif firmware_data_type == FirmwareDataType.imuQuaternion:
                print(f"Updating IMU Quaternion configuration")
                cmd = FirmwareCommand.enableImuQuaternion.id if self._state_enabled.get(firmware_data_type) else FirmwareCommand.disableImuQuaternion.id
            elif firmware_data_type == FirmwareDataType.navigation:
                print(f"Updating Navigation configuration")
                cmd = FirmwareCommand.enableNavigation.id if self._state_enabled.get(firmware_data_type) else FirmwareCommand.disableNavigation.id
            elif firmware_data_type == FirmwareDataType.embeddedGesture:
                print(f"Updating Embedded Gesture configuration")
                cmd = FirmwareCommand.enableGesture.id if self._state_enabled.get(firmware_data_type) else FirmwareCommand.disableGesture.id
            elif firmware_data_type == FirmwareDataType.embeddedPressure:
                print(f"Updating Embedded Pressure configuration")
                cmd = FirmwareCommand.enablePressure.id if self._state_enabled.get(firmware_data_type) else FirmwareCommand.disablePressure.id
            elif firmware_data_type == FirmwareDataType.embeddedAirTouch:
                print(f"Updating Embedded Air Touch configuration")
                cmd = FirmwareCommand.enableEmbeddedAirTouch.id if self._state_enabled.get(firmware_data_type) else FirmwareCommand.disableEmbeddedAirTouch.id
            else:
                print(f"Updating {firmware_data_type.name} configuration")
                
            if cmd is not None:
                await self.send_general_command(cmd)
            