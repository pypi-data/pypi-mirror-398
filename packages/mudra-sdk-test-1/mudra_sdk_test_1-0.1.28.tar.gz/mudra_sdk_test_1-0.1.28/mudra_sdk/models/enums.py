
from enum import Enum
from typing import Optional


class MudraBLEServicesUUID(Enum):
    COMMAND_SERVICE = "0000fff0-0000-1000-8000-00805f9b34fb"
    BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"
    DFU_SERVICE = "0000fe59-0000-1000-8000-00805f9b34fb"
    INFORMATION_SERVICE = "0000180a-0000-1000-8000-00805f9b34fb"

    @property
    def value_str(self) -> str:
        return self.value

    @staticmethod
    def from_value(value: str) -> Optional["MudraBLEServicesUUID"]:
        for item in MudraBLEServicesUUID:
            if item.value == value:
                return item
        return None

class MudraCharacteristicUUID(Enum):
    SNC_CHARACTERISTIC = "0000fff4-0000-1000-8000-00805f9b34fb"
    IMU_CHARACTERISTIC = "0000fff5-0000-1000-8000-00805f9b34fb"
    COMMAND_CHARACTERISTIC = "0000fff1-0000-1000-8000-00805f9b34fb"
    LOGGING_CHARACTERISTIC = "0000fff2-0000-1000-8000-00805f9b34fb"
    MESSAGE_CHARACTERISTIC = "0000fff6-0000-1000-8000-00805f9b34fb"
    BATTERY_CHARACTERISTIC = "00002a19-0000-1000-8000-00805f9b34fb"
    FIRMWARE_CHARACTERISTIC = "00002a26-0000-1000-8000-00805f9b34fb"
    SERIAL_RIGHT_PART_CHARACTERISTIC = "00002a25-0000-1000-8000-00805f9b34fb"
    SERIAL_LEFT_PART_CHARACTERISTIC = "00002a27-0000-1000-8000-00805f9b34fb"
    DFU_WITHOUT_BONDS = "8ec90003-f315-4f60-9fb8-838830daea50"
    CHARGING_STATE = "00002a1a-0000-1000-8000-00805f9b34fb"

    @property
    def value_str(self) -> str:
        return self.value

    @staticmethod
    def from_value(value: str) -> Optional["MudraCharacteristicUUID"]:
        for item in MudraCharacteristicUUID:
            if item.value == value:
                return item
        return None

class FirmwareCallbacks(Enum):
    STOP_ADVERTISING = 1
    FIRMWARE_CRASH = 2
    GESUTURE_RELEASE = 3
    FIRMWARE_STATUS = 4
    NAVIGATION_DELTA = 5
    NAVIGATION_DIRECTION = 6
    RESET_FUEL_GAUGE = 7
    PRESSURE = 8
    GESTURE_TAP = 9
    GESTURE_DOUBLE_TAP = 10
    GESTURE_TWIST = 11
    GESTURE_DOUBLE_TWIST = 12
    MAPPER_UPDATED = 13
    SAMPLE_TYPE_CHANGED = 14
    BAND_CONNECTION_STATUS = 15
    NONE = 16

    @property
    def description(self) -> str:
        return {
            FirmwareCallbacks.STOP_ADVERTISING: "StopAdvertising",
            FirmwareCallbacks.FIRMWARE_CRASH: "FirmwareCrash",
            FirmwareCallbacks.RESET_FUEL_GAUGE: "ResetFuelGauge",
            FirmwareCallbacks.GESUTURE_RELEASE: "GesutureRelease",
            FirmwareCallbacks.FIRMWARE_STATUS: "FirmwareStatus",
            FirmwareCallbacks.NAVIGATION_DELTA: "NavigationDelta",
            FirmwareCallbacks.NAVIGATION_DIRECTION: "NavigationDirection",
            FirmwareCallbacks.PRESSURE: "Pressure",
            FirmwareCallbacks.GESTURE_TAP: "GestureTap",
            FirmwareCallbacks.GESTURE_DOUBLE_TAP: "GestureDoubleTap",
            FirmwareCallbacks.GESTURE_TWIST: "GestureTwist",
            FirmwareCallbacks.GESTURE_DOUBLE_TWIST: "GestureDoubleTwist",
            FirmwareCallbacks.MAPPER_UPDATED: "mapper",
            FirmwareCallbacks.SAMPLE_TYPE_CHANGED: "sampleTypeChanged",
            FirmwareCallbacks.BAND_CONNECTION_STATUS: "bandConnectionStatus",
            FirmwareCallbacks.NONE: "none"
        }[self]

    # Static byte-array values as bytes objects
    REQUEST_FOR_MAPPER_BYTES = bytes([0x75, 0x03])
    STOP_ADVERTISING_BYTES = bytes([0x0a, 0x01])
    GESTURE_TAP_BYTES = bytes([0x61, 0x00])
    GESTURE_DOUBLE_TAP_BYTES = bytes([0x61, 0x01])
    GESTURE_TWIST_BYTES = bytes([0x61, 0x02])
    GESTURE_DOUBLE_TWIST_BYTES = bytes([0x61, 0x03])
    GESUTURE_RELEASE_BYTES = bytes([0x59, 0x00])
    RESET_FUEL_GAUGE_BYTES = bytes([0x93, 0x00])
    BAND_CONNECTION_STATUS_BYTES = bytes([0xbb, 0x01])

    MAPPER_UPDATED_LENGTH = 122

    @staticmethod
    def are_bytes_equal(bytes1: bytes, bytes2: bytes) -> bool:
        return bytes1 == bytes2

    @staticmethod
    def from_data(data: bytes) -> "FirmwareCallbacks":
        if len(data) >= 2 and FirmwareCallbacks.are_bytes_equal(data[:2], FirmwareCallbacks.STOP_ADVERTISING_BYTES.value):
            return FirmwareCallbacks.STOP_ADVERTISING
        if data and data[0] == 0x63:
            return FirmwareCallbacks.FIRMWARE_CRASH
        if data and data[0] == 0x03 and len(data) == FirmwareCallbacks.MAPPER_UPDATED_LENGTH:
            return FirmwareCallbacks.MAPPER_UPDATED
        if data and data[0] in (0x01, 0x02):
            return FirmwareCallbacks.FIRMWARE_STATUS
        if data and data[0] == 0x60:
            return FirmwareCallbacks.PRESSURE
        if len(data) >= 2 and FirmwareCallbacks.are_bytes_equal(data[:2], FirmwareCallbacks.GESTURE_TAP_BYTES.value):
            return FirmwareCallbacks.GESTURE_TAP
        if len(data) >= 2 and FirmwareCallbacks.are_bytes_equal(data[:2], FirmwareCallbacks.GESTURE_DOUBLE_TAP_BYTES.value):
            return FirmwareCallbacks.GESTURE_DOUBLE_TAP
        if len(data) >= 2 and FirmwareCallbacks.are_bytes_equal(data[:2], FirmwareCallbacks.GESTURE_TWIST_BYTES.value):
            return FirmwareCallbacks.GESTURE_TWIST
        if len(data) >= 2 and FirmwareCallbacks.are_bytes_equal(data[:2], FirmwareCallbacks.GESTURE_DOUBLE_TWIST_BYTES.value):
            return FirmwareCallbacks.GESTURE_DOUBLE_TWIST
        if len(data) >= 2 and FirmwareCallbacks.are_bytes_equal(data[:2], FirmwareCallbacks.GESUTURE_RELEASE_BYTES.value):
            return FirmwareCallbacks.GESUTURE_RELEASE
        if data and data[0] == 0x64:
            return FirmwareCallbacks.NAVIGATION_DELTA
        if data and data[0] == 0x22:
            return FirmwareCallbacks.SAMPLE_TYPE_CHANGED
        if data and data[0] == 0x65:
            return FirmwareCallbacks.NAVIGATION_DIRECTION
        if len(data) >= 2 and FirmwareCallbacks.are_bytes_equal(data[:2], FirmwareCallbacks.RESET_FUEL_GAUGE_BYTES.value):
            return FirmwareCallbacks.RESET_FUEL_GAUGE
        if len(data) >= 2 and FirmwareCallbacks.are_bytes_equal(data[:2], FirmwareCallbacks.BAND_CONNECTION_STATUS_BYTES.value):
            return FirmwareCallbacks.BAND_CONNECTION_STATUS
        return FirmwareCallbacks.NONE


class GestureGroup(Enum):
    GESTURE = "gesture"
    MOTION = "motion"

class GestureType(Enum):
    TAP = 0x00
    DOUBLE_TAP = 0x01
    TWIST = 0x02
    DOUBLE_TWIST = 0x03
    LEFT_PINCH = 0x04
    RIGHT_PINCH = 0x05
    UP_PINCH = 0x06
    DOWN_PINCH = 0x07
    REVERSE_LEFT_PINCH = 0x08
    REVERSE_RIGHT_PINCH = 0x09
    REVERSE_UP_PINCH = 0x0a
    REVERSE_DOWN_PINCH = 0x0b
    REVERSE_PINCH = 0x0c
    REVERSE_DOUBLE_TAP = 0x0d
    PINCH_ROLL_LEFT = 0x0e
    PINCH_ROLL_RIGHT = 0x0f
    PINCH_IN = 0x10
    PINCH_OUT = 0x11
    SHORT_TAP = 0x12
    REVERSE_TAP = 0x13

    @property
    def value_int(self):
        # To mirror Dart's .value int getter (just more explicit)
        return self.value

    @property
    def gesture_group(self):
        # Mirrors the gestureGroup getter in Dart
        if self in (
            GestureType.LEFT_PINCH,
            GestureType.RIGHT_PINCH,
            GestureType.UP_PINCH,
            GestureType.DOWN_PINCH,
            GestureType.REVERSE_LEFT_PINCH,
            GestureType.REVERSE_RIGHT_PINCH,
            GestureType.REVERSE_UP_PINCH,
            GestureType.REVERSE_DOWN_PINCH,
            GestureType.PINCH_ROLL_LEFT,
            GestureType.PINCH_ROLL_RIGHT,
            GestureType.PINCH_IN,
            GestureType.PINCH_OUT
        ):
            return GestureGroup.MOTION
        elif self in (
            GestureType.TAP,
            GestureType.DOUBLE_TAP,
            GestureType.TWIST,
            GestureType.DOUBLE_TWIST,
            GestureType.REVERSE_PINCH,
            GestureType.REVERSE_DOUBLE_TAP,
            GestureType.SHORT_TAP,
            GestureType.REVERSE_TAP,
        ):
            return GestureGroup.GESTURE
        else:
            return None

    @property
    def description(self):
        return {
            GestureType.TAP: "Tap",
            GestureType.DOUBLE_TAP: "Double Tap",
            GestureType.TWIST: "Twist",
            GestureType.DOUBLE_TWIST: "Double Twist",
            GestureType.LEFT_PINCH: "Left Pinch",
            GestureType.RIGHT_PINCH: "Right Pinch",
            GestureType.UP_PINCH: "Up Pinch",
            GestureType.DOWN_PINCH: "Down Pinch",
            GestureType.REVERSE_LEFT_PINCH: "Reverse Left Pinch",
            GestureType.REVERSE_RIGHT_PINCH: "Reverse Right Pinch",
            GestureType.REVERSE_UP_PINCH: "Reverse Up Pinch",
            GestureType.REVERSE_DOWN_PINCH: "Reverse Down Pinch",
            GestureType.REVERSE_PINCH: "Reverse Pinch",
            GestureType.REVERSE_DOUBLE_TAP: "Reverse Double Tap",
            GestureType.PINCH_ROLL_LEFT: "Pinch Roll Left",
            GestureType.PINCH_ROLL_RIGHT: "Pinch Roll Right",
            GestureType.PINCH_IN: "Pinch In",
            GestureType.PINCH_OUT: "Pinch Out",
            GestureType.SHORT_TAP: "Short Tap",
            GestureType.REVERSE_TAP: "Reverse Tap",
        }[self]

    @staticmethod
    def from_value(value: int) -> "GestureType":
        for type_ in GestureType:
            if type_.value == value:
                return type_
        raise ValueError(f"Invalid value for GestureType: {value:#04x}")

class ScrollDirection(Enum):
    normal = 0x00
    reverse = 0xFF

    @property
    def op_code(self) -> int:
        if self == ScrollDirection.normal:
            return 0x00
        elif self == ScrollDirection.reverse:
            return 0xFF

    @staticmethod
    def from_value(value: int) -> "ScrollDirection":
        if value == 0x00:
            return ScrollDirection.normal
        elif value == 0xFF:
            return ScrollDirection.reverse
        return ScrollDirection.reverse


class MapperMode(Enum):
    mouseMapper = 0x00
    keyboardMapper = 0x01

    @property
    def op_code(self) -> int:
        if self == MapperMode.mouseMapper:
            return 0x00
        elif self == MapperMode.keyboardMapper:
            return 0x01

    @staticmethod
    def from_value(value: int) -> "MapperMode":
        if value == 0x00:
            return MapperMode.mouseMapper
        elif value == 0x01:
            return MapperMode.keyboardMapper
        return MapperMode.mouseMapper


class BandMode(Enum):
    mudraBand = 0x00
    mudraLink = 0x01

    @property
    def op_code(self) -> int:
        if self == BandMode.mudraBand:
            return 0x00
        elif self == BandMode.mudraLink:
            return 0x01

    @staticmethod
    def from_value(value: int) -> "BandMode":
        if value == 0x00:
            return BandMode.mudraBand
        elif value == 0x01:
            return BandMode.mudraLink
        return None


class HandType(Enum):
    left = 0x00
    right = 0x01

    @property
    def op_code(self) -> int:
        if self == HandType.left:
            return 0x00
        elif self == HandType.right:
            return 0x01

class AirTouchButton(Enum):
    release = 0
    press = 1

    @property
    def description(self) -> str:
        if self == AirTouchButton.release:
            return "Release"
        elif self == AirTouchButton.press:
            return "Press"

    @staticmethod
    def from_value(value: int) -> "AirTouchButton":
        if value == 0:
            return AirTouchButton.release
        return AirTouchButton.press



class FirmwareDataType(Enum):
    snc = 0
    imuQuaternion = 2
    imuGyro = 3
    imuAccelometer = 4
    navigation = 5
    embeddedGesture = 6
    embeddedPressure = 7
    embeddedAirTouch = 8

    @property
    def value_int(self) -> int:
        return self.value

    @staticmethod
    def from_value(value: int) -> "FirmwareDataType":
        for item in FirmwareDataType:
            if item.value == value:
                return item
        return None

class ModelType(Enum):
    basic = 0
    basicWithoutQuaternion = 1
    neuralClicker = 2
    embedded = 3
    weightEstimation = 4

    @property
    def value_int(self) -> int:
        return self.value

    @staticmethod
    def from_value(value: int) -> "ModelType":
        for item in ModelType:
            if item.value == value:
                return item
        return None


class FirmwareCommand(Enum):
    enableSnc = 0
    disableSnc = 1
    getSerialNumber = 2
    enableImuNorm = 3
    disableImuNorm = 4
    enableImuQuaternion = 5
    disableImuQuaternion = 6
    enableImuGyro = 7
    disableImuGyro = 8
    enableImuAccRaw = 9
    disableImuAccRaw = 10
    getFirmwareVersion = 11
    getSecondaryDevicesState = 12
    pairSecondaryDevice = 13
    unpairSecondaryDevice = 14
    changeSecondaryDevice = 15
    enableGesture = 16
    disableGesture = 17
    enablePressure = 18
    disablePressure = 19
    enableNavigation = 20
    disableNavigation = 21
    enableEmbeddedAirTouch = 22
    disableEmbeddedAirTouch = 23
    getGeneralStatus = 24
    getAirMouseStatus = 25
    setSampleType = 26
    resetFuelGauge = 27
    sendFirmwareOutputTo = 28
    setDeviceMode = 29
    setBandMode = 30
    setMapperMode = 31
    resetMapperMode = 32
    airMouseSpeed = 33
    resetAirMouse = 34
    objectScale = 35
    recenterImuCubic = 36
    stopAdvertising = 37
    buttonsCommand = 38
    keyBoardCommand = 39
    handType = 40
    genericCommand = 41
    shippingMode = 42
    batteryInformation = 43
    updateHidMapping = 44
    getMouseHidMapper = 45
    getKeyboardHidMapper = 46
    enterToDfuMode = 47
    scrollSpeed = 48
    hidFrequency = 49
    scrollDirection = 50
    getScrollDirection = 51
    getMapperMode = 52

    @property
    def description(self) -> str:
        return {
            FirmwareCommand.enableSnc: "EnableSnc",
            FirmwareCommand.disableSnc: "DisableSnc",
            FirmwareCommand.getSerialNumber: "GetSerialNumber",
            FirmwareCommand.enableImuNorm: "EnableImuNorm",
            FirmwareCommand.disableImuNorm: "DisableImuNorm",
            FirmwareCommand.enableImuQuaternion: "EnableImuQuaternion",
            FirmwareCommand.disableImuQuaternion: "DisableImuQuaternion",
            FirmwareCommand.enableImuGyro: "EnableImuGyro",
            FirmwareCommand.disableImuGyro: "DisableImuGyro",
            FirmwareCommand.enableImuAccRaw: "EnableImuAccRaw",
            FirmwareCommand.disableImuAccRaw: "DisableImuAccRaw",
            FirmwareCommand.getFirmwareVersion: "GetFirmwareVersion",
            FirmwareCommand.getSecondaryDevicesState: "GetSecondaryDevicesState",
            FirmwareCommand.pairSecondaryDevice: "PairSecondaryDevice",
            FirmwareCommand.unpairSecondaryDevice: "UnpairSecondaryDevice",
            FirmwareCommand.changeSecondaryDevice: "ChangeSecondaryDevice",
            FirmwareCommand.enableGesture: "EnableGesture",
            FirmwareCommand.disableGesture: "DisableGesture",
            FirmwareCommand.enablePressure: "EnablePressure",
            FirmwareCommand.disablePressure: "DisablePressure",
            FirmwareCommand.enableNavigation: "EnableNavigation",
            FirmwareCommand.disableNavigation: "DisableNavigation",
            FirmwareCommand.enableEmbeddedAirTouch: "EnableEmbeddedAirTouch",
            FirmwareCommand.disableEmbeddedAirTouch: "DisableEmbeddedAirTouch",
            FirmwareCommand.getGeneralStatus: "GetGeneralStatus",
            FirmwareCommand.getAirMouseStatus: "GetAirMouseStatus",
            FirmwareCommand.setSampleType: "SetSampleType",
            FirmwareCommand.resetFuelGauge: "ResetFuelGauge",
            FirmwareCommand.sendFirmwareOutputTo: "SendFirmwareOutputTo",
            FirmwareCommand.setDeviceMode: "SetDeviceMode",
            FirmwareCommand.setBandMode: "SetBandMode",
            FirmwareCommand.setMapperMode: "SetMapperMode",
            FirmwareCommand.resetMapperMode: "ResetMapperMode",
            FirmwareCommand.airMouseSpeed: "AirMouseSpeed",
            FirmwareCommand.resetAirMouse: "ResetAirMouse",
            FirmwareCommand.objectScale: "ObjectScale",
            FirmwareCommand.recenterImuCubic: "RecenterImuCubic",
            FirmwareCommand.stopAdvertising: "StopAdvertising",
            FirmwareCommand.buttonsCommand: "ButtonsCommand",
            FirmwareCommand.keyBoardCommand: "KeyBoardCommand",
            FirmwareCommand.handType: "HandType",
            FirmwareCommand.genericCommand: "GenericCommand",
            FirmwareCommand.shippingMode: "ShippingMode",
            FirmwareCommand.batteryInformation: "BatteryInformation",
            FirmwareCommand.updateHidMapping: "UpdateHIDMapping",
            FirmwareCommand.getMouseHidMapper: "GetMouseHidMapper",
            FirmwareCommand.getKeyboardHidMapper: "GetKeyboardHidMapper",
            FirmwareCommand.enterToDfuMode: "EnterToDfuMode",
            FirmwareCommand.scrollSpeed: "ScrollSpeed",
            FirmwareCommand.hidFrequency: "HidFrequency",
            FirmwareCommand.scrollDirection: "ScrollDirection",
            FirmwareCommand.getScrollDirection: "GetScrollDirection",
            FirmwareCommand.getMapperMode: "GetMapperMode",
        }[self]

    @property
    def op_code(self) -> int:
        return self.value

    @property
    def id(self) -> bytes:
        from mudra_sdk.models.computation_wrapper import ComputationWrapper
        return ComputationWrapper.get_firmware_command_bytes(self.op_code)

    @staticmethod
    def from_value(value: int) -> Optional["FirmwareCommand"]:
        for item in FirmwareCommand:
            if item.value == value:
                return item
        return None

