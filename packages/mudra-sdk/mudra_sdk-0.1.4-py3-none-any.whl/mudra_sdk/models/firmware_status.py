from typing import Optional, List, Any
from .enums import MapperMode, HandType, BandMode, ScrollDirection

# Dummy logger as Python equivalent for AppLoggers.firmwareStatus
class _DummyLogger:
    def debug(self, msg: str):
        print(msg)

class FirmwareStatus:
    _logger = _DummyLogger()

    # Status byte arrays
    general_status: Optional[List[int]]
    air_mouse_status: Optional[List[int]]

    # Firmware general status indexes
    SNC_ENABLED_INDEX = 14
    ACC_ENABLED_INDEX = 6
    GYRO_ENABLED_INDEX = 5
    QUATERNION_ENABLED_INDEX = 4
    NAVIGATION_ENABLED_INDEX = 10
    GESTURE_ENABLED_INDEX = 11
    PRESSURE_ENABLED_INDEX = 15
    AIR_TOUCH_ENABLED_INDEX = 19

    # Air mouse status indexes
    DEVICE_MODE_INDEX = 1
    SENDS_NAVIGATION_TO_HID_ENABLED_INDEX = 2
    SENDS_NAVIGATION_TO_APP_ENABLED_INDEX = 3
    SENDS_GESTURE_TO_HID_ENABLED_INDEX = 4
    CURRENT_MAPPER_MODE_INDEX = 5
    HAND_INDEX = 9
    POINTER_SPEED_X_INDEX = 10
    POINTER_SPEED_Y_INDEX = 11
    HID_FREQUENCY_INDEX = 14
    SCROLL_SPEED_INDEX = 15
    SCROLL_DIRECTION_INDEX = 16
    BAND_MODE_INDEX = 17

    def __init__(self):
        self.general_status = None
        self.air_mouse_status = None

    def update(self, data: bytes):
        if not data:
            return
        d = list(data)
        if d[0] == 1:
            old_status = self.general_status
            self.general_status = d

            if old_status is not None:
                if old_status[self.NAVIGATION_ENABLED_INDEX] != d[self.NAVIGATION_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : Navigation enabled changed: {d[self.NAVIGATION_ENABLED_INDEX] == 1}")
                if old_status[self.GESTURE_ENABLED_INDEX] != d[self.GESTURE_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : Gesture enabled changed: {d[self.GESTURE_ENABLED_INDEX] == 1}")
                if old_status[self.PRESSURE_ENABLED_INDEX] != d[self.PRESSURE_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : Pressure enabled changed: {d[self.PRESSURE_ENABLED_INDEX] == 1}")
                if old_status[self.SNC_ENABLED_INDEX] != d[self.SNC_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : SNC enabled changed: {d[self.SNC_ENABLED_INDEX] == 1}")
                if old_status[self.ACC_ENABLED_INDEX] != d[self.ACC_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : Accelerometer enabled changed: {d[self.ACC_ENABLED_INDEX] == 1}")
                if old_status[self.GYRO_ENABLED_INDEX] != d[self.GYRO_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : Gyro enabled changed: {d[self.GYRO_ENABLED_INDEX] == 1}")
                if old_status[self.QUATERNION_ENABLED_INDEX] != d[self.QUATERNION_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : Quaternion enabled changed: {d[self.QUATERNION_ENABLED_INDEX] == 1}")
                if old_status[self.AIR_TOUCH_ENABLED_INDEX] != d[self.AIR_TOUCH_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : AirTouch enabled changed: {d[self.AIR_TOUCH_ENABLED_INDEX] == 1}")
        elif d[0] == 2:
            old_status = self.air_mouse_status
            self.air_mouse_status = d

            if old_status is not None:
                if old_status[self.DEVICE_MODE_INDEX] != d[self.DEVICE_MODE_INDEX]:
                    self._logger.debug(f"Firmware status : Device mode changed: {d[self.DEVICE_MODE_INDEX]}")
                if old_status[self.SENDS_NAVIGATION_TO_APP_ENABLED_INDEX] != d[self.SENDS_NAVIGATION_TO_APP_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : Sends navigation to app changed: {d[self.SENDS_NAVIGATION_TO_APP_ENABLED_INDEX] == 1}")
                if old_status[self.SENDS_NAVIGATION_TO_HID_ENABLED_INDEX] != d[self.SENDS_NAVIGATION_TO_HID_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : Sends navigation to HID changed: {d[self.SENDS_NAVIGATION_TO_HID_ENABLED_INDEX] == 1}")
                if old_status[self.SENDS_GESTURE_TO_HID_ENABLED_INDEX] != d[self.SENDS_GESTURE_TO_HID_ENABLED_INDEX]:
                    self._logger.debug(f"Firmware status : Sends gesture to HID changed: {d[self.SENDS_GESTURE_TO_HID_ENABLED_INDEX] == 1}")
                if old_status[self.CURRENT_MAPPER_MODE_INDEX] != d[self.CURRENT_MAPPER_MODE_INDEX]:
                    self._logger.debug(f"Firmware status : mapper changed: {MapperMode.from_value(d[self.CURRENT_MAPPER_MODE_INDEX])}")
                if old_status[self.HAND_INDEX] != d[self.HAND_INDEX]:
                    self._logger.debug(f"Firmware status : hand changed: {'left' if d[self.HAND_INDEX] == 1 else 'right'}")
                if old_status[self.POINTER_SPEED_X_INDEX] != d[self.POINTER_SPEED_X_INDEX]:
                    self._logger.debug(f"Firmware status : pointer speed x changed: {d[self.POINTER_SPEED_X_INDEX]}")
                if old_status[self.POINTER_SPEED_Y_INDEX] != d[self.POINTER_SPEED_Y_INDEX]:
                    self._logger.debug(f"Firmware status : pointer speed y changed: {d[self.POINTER_SPEED_Y_INDEX]}")
                if old_status[self.SCROLL_SPEED_INDEX] != d[self.SCROLL_SPEED_INDEX]:
                    self._logger.debug(f"Firmware status : scrollSpeed changed: {d[self.SCROLL_SPEED_INDEX]}")
                if old_status[self.HID_FREQUENCY_INDEX] != d[self.HID_FREQUENCY_INDEX]:
                    self._logger.debug(f"Firmware status : hidFrequency changed: {d[self.HID_FREQUENCY_INDEX]}")
                if old_status[self.SCROLL_DIRECTION_INDEX] != d[self.SCROLL_DIRECTION_INDEX]:
                    self._logger.debug(f"Firmware status : scrollDirection changed: {d[self.SCROLL_DIRECTION_INDEX]}")
                if old_status[self.BAND_MODE_INDEX] != d[self.BAND_MODE_INDEX]:
                    self._logger.debug(f"Firmware status : bandMode changed: {d[self.BAND_MODE_INDEX]}")

    @property
    def is_navigation_enabled(self) -> bool:
        return bool(self.general_status and self.general_status[self.NAVIGATION_ENABLED_INDEX] == 1)

    @property
    def device_mode(self) -> int:
        if self.air_mouse_status:
            return self.air_mouse_status[self.DEVICE_MODE_INDEX]
        return -1

    @property
    def is_gesture_enabled(self) -> bool:
        return bool(self.general_status and self.general_status[self.GESTURE_ENABLED_INDEX] == 1)

    @property
    def is_pressure_enabled(self) -> bool:
        return bool(self.general_status and self.general_status[self.PRESSURE_ENABLED_INDEX] == 1)

    @property
    def is_snc_enabled(self) -> bool:
        return bool(self.general_status and self.general_status[self.SNC_ENABLED_INDEX] == 1)

    @property
    def is_acc_enabled(self) -> bool:
        return bool(self.general_status and self.general_status[self.ACC_ENABLED_INDEX] == 1)

    @property
    def is_gyro_enabled(self) -> bool:
        return bool(self.general_status and self.general_status[self.GYRO_ENABLED_INDEX] == 1)

    @property
    def is_quaternion_enabled(self) -> bool:
        return bool(self.general_status and self.general_status[self.QUATERNION_ENABLED_INDEX] == 1)

    @property
    def is_sends_navigation_to_app_enabled(self) -> bool:
        return bool(self.air_mouse_status and self.air_mouse_status[self.SENDS_NAVIGATION_TO_APP_ENABLED_INDEX] == 1)

    @property
    def is_sends_navigation_to_hid_enabled(self) -> bool:
        return bool(self.air_mouse_status and self.air_mouse_status[self.SENDS_NAVIGATION_TO_HID_ENABLED_INDEX] == 1)

    @property
    def is_sends_gesture_to_hid_enabled(self) -> bool:
        return bool(self.air_mouse_status and self.air_mouse_status[self.SENDS_GESTURE_TO_HID_ENABLED_INDEX] == 1)

    @property
    def is_air_touch_enabled(self) -> bool:
        return bool(self.general_status and self.general_status[self.AIR_TOUCH_ENABLED_INDEX] == 1)

    @property
    def hand_type(self) -> HandType:
        if self.air_mouse_status and self.air_mouse_status[self.HAND_INDEX] == 1:
            return HandType.left
        else:
            return HandType.right

    @property
    def pointer_speed_x(self) -> int:
        if self.air_mouse_status:
            return self.air_mouse_status[self.POINTER_SPEED_X_INDEX]
        return 0

    @property
    def pointer_speed_y(self) -> int:
        if self.air_mouse_status:
            return self.air_mouse_status[self.POINTER_SPEED_Y_INDEX]
        return 0

    @property
    def scroll_speed(self) -> Optional[int]:
        if self.air_mouse_status:
            return self.air_mouse_status[self.SCROLL_SPEED_INDEX]
        return None

    @property
    def hid_frequency(self) -> Optional[int]:
        if self.air_mouse_status:
            return self.air_mouse_status[self.HID_FREQUENCY_INDEX]
        return None

    @property
    def band_mode(self) -> Optional[BandMode]:
        if self.air_mouse_status:
            return BandMode.from_value(self.air_mouse_status[self.BAND_MODE_INDEX])
        return None

    @property
    def current_mapper_mode(self) -> MapperMode:
        if self.air_mouse_status:
            return MapperMode.from_value(self.air_mouse_status[self.CURRENT_MAPPER_MODE_INDEX])
        return MapperMode.from_value(0)

    @property
    def scroll_direction(self) -> ScrollDirection:
        if self.air_mouse_status and self.air_mouse_status[self.SCROLL_DIRECTION_INDEX] == 1:
            return ScrollDirection.normal
        else:
            return ScrollDirection.reverse
