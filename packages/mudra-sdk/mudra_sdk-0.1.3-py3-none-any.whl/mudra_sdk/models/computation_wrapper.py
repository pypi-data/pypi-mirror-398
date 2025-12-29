from ctypes import POINTER, c_float, c_int, c_void_p, c_char_p, c_uint8, c_int32, c_size_t, Structure
import ctypes
from typing import Callable, List, Optional
from mudra_sdk.models.enums import AirTouchButton, GestureType, ModelType
import mudra_sdk.models.mudra as mudraModule


OnGestureDataReceivedCallback = Callable[[GestureType], None]
OnAirTouchButtonChangedReceivedCallback = Callable[[AirTouchButton], None]
OnNavigationDeltaReceivedCallback = Callable[[int, int], None]


ComputationHandle = c_void_p
OnRawDataCallback = Callable[[int, List[float], int, float, List[float]], None]
OnRawDataCallbackC = ctypes.CFUNCTYPE(None, c_int, POINTER(c_float), c_int, c_int, c_float, POINTER(c_float))

OnPressureCallback = Callable[[int], None]
OnPressureCallbackC = ctypes.CFUNCTYPE(None, c_float)


class ByteBuffer(Structure):
    _fields_ = [
        ("data", POINTER(c_uint8)),
        ("length", c_size_t),
    ]


class ComputationWrapper:
    _native_lib = None
    _snc_rms_count = 3
    
    def __init__(self, index: int, model_path: str = "./", writable_path: str = "./"):
        self._ensure_native_lib_loaded()
        self._initialize_native_lib()

        self._handle = self._native_lib.create_computation(
            index,
            model_path.encode(),
            writable_path.encode(),
        )
        if not self._handle:
            raise RuntimeError("Failed to create computation")

    @classmethod
    def _ensure_native_lib_loaded(cls):
        if cls._native_lib is None:
            cls._native_lib = mudraModule.Mudra().get_native_library()
        if cls._native_lib is None:
            raise RuntimeError("Native library is not loaded")

    def _initialize_native_lib(self):
        lib = self._native_lib
        
        lib.create_computation.argtypes = [c_int, c_char_p, c_char_p]
        lib.create_computation.restype = ComputationHandle

        lib.handle_data.argtypes = [ComputationHandle, POINTER(c_uint8), c_int32]
        lib.handle_data.restype = None

        lib.is_data_needed.argtypes = [ComputationHandle, c_int]
        lib.is_data_needed.restype = ctypes.c_bool

        lib.set_on_snc_ready.argtypes = [ComputationHandle, OnRawDataCallbackC]
        lib.set_on_snc_ready.restype = None

        lib.set_on_imu_acc_ready.argtypes = [ComputationHandle, OnRawDataCallbackC]
        lib.set_on_imu_acc_ready.restype = None

        lib.set_on_imu_gyro_ready.argtypes = [ComputationHandle, OnRawDataCallbackC]
        lib.set_on_imu_gyro_ready.restype = None

        lib.set_on_pressure_ready.argtypes = [ComputationHandle, OnPressureCallbackC]
        lib.set_on_pressure_ready.restype = None

        lib.set_model_type.argtypes = [ComputationHandle, c_int]
        lib.set_model_type.restype = None

        lib.set_license.argtypes = [c_char_p]
        lib.set_license.restype = None

        lib.get_firmware_command.argtypes = [c_int32]
        lib.get_firmware_command.restype = ByteBuffer

        lib.free_firmware_buffer.argtypes = [POINTER(c_uint8)]
        lib.free_firmware_buffer.restype = None


    def is_data_needed(self, index: int) -> bool:
        return bool(self._native_lib.is_data_needed(self._handle, index))

    def handle_data(self, data: bytes, length: int) -> None:
        buf = (c_uint8 * length).from_buffer_copy(data)
        self._native_lib.handle_data(self._handle, buf, c_int32(length))

    def _create_raw_callback_wrapper(self, callback: OnRawDataCallback, rms_count: int = 0):
        def _native_cb(
            timestamp: int,
            data_ptr: POINTER(c_float),
            data_len: int,
            frequency: int,
            frequency_std: float,
            rms_ptr: POINTER(c_float),
        ):
            data = [data_ptr[i] for i in range(data_len)]
            rms = [rms_ptr[i] for i in range(rms_count)] if rms_count > 0 else []
            callback(timestamp, data, frequency, frequency_std, rms)
        return OnRawDataCallbackC(_native_cb)

    def _set_raw_callback(self, setter_func, callback: OnRawDataCallback | None, rms_count: int = 0):
        if callback is None:
            setter_func(self._handle, ctypes.cast(0, OnRawDataCallbackC))
            return None
        callback_ref = self._create_raw_callback_wrapper(callback, rms_count)
        setter_func(self._handle, callback_ref)
        return callback_ref

    def set_on_snc_ready(self, callback: OnRawDataCallback | None) -> None:
        self._snc_callback_ref = self._set_raw_callback(
            self._native_lib.set_on_snc_ready, callback, self._snc_rms_count
        )

    def set_on_imu_acc_ready(self, callback: OnRawDataCallback | None) -> None:
        self._imu_acc_callback_ref = self._set_raw_callback(
            self._native_lib.set_on_imu_acc_ready, callback, 0
        )

    def set_on_imu_gyro_ready(self, callback: OnRawDataCallback | None) -> None:
        self._imu_gyro_callback_ref = self._set_raw_callback(
            self._native_lib.set_on_imu_gyro_ready, callback, 0
        )

    def set_on_pressure_ready(self, callback: OnPressureCallback | None) -> None:
        if callback is None:
            self._native_lib.set_on_pressure_ready(self._handle, ctypes.cast(0, OnPressureCallbackC))
            return None
        def _native_cb(pressure_data: float):
            callback(pressure_data)
        callback_ref = OnPressureCallbackC(_native_cb)
        self._native_lib.set_on_pressure_ready(self._handle, callback_ref)

    @staticmethod
    def set_license(license_name: str):
        ComputationWrapper._ensure_native_lib_loaded()
        ComputationWrapper._native_lib.set_license(license_name.encode())

    def set_model_type(self, model_type: ModelType):
        self._native_lib.set_model_type(self._handle, c_int(model_type.value_int))

    @staticmethod
    def get_firmware_command_bytes(command: int) -> bytes:
        buf = ComputationWrapper._native_lib.get_firmware_command(c_int32(command))

        array_ptr = ctypes.cast(buf.data, POINTER(c_uint8 * buf.length))
        result = bytes(array_ptr.contents)
        
        ComputationWrapper._native_lib.free_firmware_buffer(buf.data)
        return result