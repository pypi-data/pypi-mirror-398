"""
LPAMSDK Python wrapper using ctypes.

"""

import os
import sys
import ctypes
from ctypes import c_longlong, c_int, c_uint, c_double, c_char, POINTER, byref

# Add the DLL directory to the path so dependencies can be found
dll_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dll")
os.environ['PATH'] = dll_dir + os.pathsep + os.environ['PATH']

# Define the path to the DLL
_DLL_PATH = os.path.join(dll_dir, "lpamsdk.dll")

# Check if the DLL exists
if not os.path.exists(_DLL_PATH):
    raise ImportError(f"LPAMSDK DLL not found at: {_DLL_PATH}")

# Print helpful information
print(f"LPAMSDK: Using DLL at {_DLL_PATH}")
print(f"LPAMSDK: Python architecture: {sys.maxsize > 2**32 and '64-bit' or '32-bit'}")

# Check if libusb-1.0.dll exists (it's a dependency)
_libusb_path = os.path.join(dll_dir, "libusb-1.0.dll")
if not os.path.exists(_libusb_path):
    print(f"Warning: libusb-1.0.dll not found at: {_libusb_path}")
    print("This might cause issues with USB devices.")

# Try to load the DLL with detailed error handling
_loaded = False
_lpamsdk = None

try:
    # Try both CDLL and WinDLL with detailed error handling
    from ctypes import WinError
    
    # Try CDLL
    try:
        _lpamsdk = ctypes.CDLL(_DLL_PATH)
        print(f"LPAMSDK: DLL loaded successfully as CDLL")
        _loaded = True
    except OSError as e:
        # Try WinDLL
        try:
            _lpamsdk = ctypes.WinDLL(_DLL_PATH)
            print(f"LPAMSDK: DLL loaded successfully as WinDLL")
            _loaded = True
        except OSError as e2:
            # Provide detailed error information and solutions
            print("\nLPAMSDK: ERROR - Failed to load DLL")
            print(f"  Reason: {e2}")
            print(f"  Windows error code: {WinError().winerror}")
            print("\nPOSSIBLE SOLUTIONS:")
            print("1. Missing Dependencies:")
            print("   - Install Visual C++ Redistributable for Visual Studio (2015-2022 or newer)")
            print("   - Use Dependency Walker (depends.exe) to identify missing DLLs")
            print("   - Ensure libusb-1.0.dll/pthreadVC2.dll is in the same directory as lpamsdk.dll")
            print("2. Architecture Mismatch:")
            print("   - Ensure all DLLs (lpamsdk.dll, libusb-1.0.dll, pthreadVC2.dll) are the same bitness")
            print("   - Ensure Python and DLLs are same bitness (32-bit or 64-bit)")
            
            # Raise the error to maintain backward compatibility
            raise ImportError(f"Failed to load LPAMSDK DLL: {e2}")
    
    # Check if the functions are available
    _functions_available = True
    
    # Enumerations
    class DaqDeviceInterface:
        """Device interface types"""
        USB_IFC = 1 << 0
        BLUETOOTH_IFC = 1 << 1
        ETHERNET_IFC = 1 << 2
        ANY_IFC = USB_IFC | BLUETOOTH_IFC | ETHERNET_IFC

    class UlError:
        """LPAMSDK error codes"""
        ERR_NO_ERROR = 0
        ERR_UNHANDLED_EXCEPTION = 1
        ERR_BAD_DEV_HANDLE = 2
        ERR_BAD_DEV_TYPE = 3
        ERR_USB_DEV_NO_PERMISSION = 4
        ERR_USB_INTERFACE_CLAIMED = 5
        ERR_DEV_NOT_FOUND = 6
        ERR_DEV_NOT_CONNECTED = 7
        ERR_DEAD_DEV = 8
        ERR_BAD_BUFFER_SIZE = 9
        ERR_BAD_BUFFER = 10
        ERR_BAD_MEM_TYPE = 11
        ERR_BAD_MEM_REGION = 12
        ERR_BAD_RANGE = 13
        ERR_BAD_AI_CHAN = 14
        ERR_BAD_INPUT_MODE = 15
        ERR_ALREADY_ACTIVE = 16
        ERR_BAD_TRIG_TYPE = 17
        ERR_OVERRUN = 18
        ERR_UNDERRUN = 19
        ERR_TIMEDOUT = 20
        ERR_BAD_OPTION = 21
        ERR_BAD_RATE = 22
        ERR_BAD_BURSTIO_COUNT = 23
        ERR_CONFIG_NOT_SUPPORTED = 24
        ERR_BAD_CONFIG_VAL = 25
        ERR_BAD_AI_CHAN_TYPE = 26
        ERR_ADC_OVERRUN = 27
        ERR_BAD_TC_TYPE = 28
        ERR_BAD_UNIT = 29
        ERR_BAD_QUEUE_SIZE = 30
        ERR_BAD_CONFIG_ITEM = 31
        ERR_BAD_INFO_ITEM = 32
        ERR_BAD_FLAG = 33
        ERR_BAD_SAMPLE_COUNT = 34
        ERR_INTERNAL = 35
        ERR_BAD_COUPLING_MODE = 36
        ERR_BAD_SENSOR_SENSITIVITY = 37
        ERR_BAD_IEPE_MODE = 38
        ERR_BAD_AI_CHAN_QUEUE = 39
        ERR_BAD_AI_GAIN_QUEUE = 40
        ERR_BAD_AI_MODE_QUEUE = 41
        ERR_FPGA_FILE_NOT_FOUND = 42
        ERR_UNABLE_TO_READ_FPGA_FILE = 43
        ERR_NO_FPGA = 44
        ERR_BAD_ARG = 45
        ERR_MIN_SLOPE_VAL_REACHED = 46
        ERR_MAX_SLOPE_VAL_REACHED = 47
        ERR_MIN_OFFSET_VAL_REACHED = 48
        ERR_MAX_OFFSET_VAL_REACHED = 49
        ERR_BAD_PORT_TYPE = 50
        ERR_WRONG_DIG_CONFIG = 51
        ERR_BAD_BIT_NUM = 52
        ERR_BAD_PORT_VAL = 53
        ERR_BAD_RETRIG_COUNT = 54
        ERR_BAD_AO_CHAN = 55
        ERR_BAD_DA_VAL = 56
        ERR_BAD_TMR = 57
        ERR_BAD_FREQUENCY = 58
        ERR_BAD_DUTY_CYCLE = 59
        ERR_BAD_INITIAL_DELAY = 60
        ERR_BAD_CTR = 61
        ERR_BAD_CTR_VAL = 62
        ERR_BAD_DAQI_CHAN_TYPE = 63
        ERR_BAD_NUM_CHANS = 64
        ERR_BAD_CTR_REG = 65
        ERR_BAD_CTR_MEASURE_TYPE = 66
        ERR_BAD_CTR_MEASURE_MODE = 67
        ERR_BAD_DEBOUNCE_TIME = 68
        ERR_BAD_DEBOUNCE_MODE = 69
        ERR_BAD_EDGE_DETECTION = 70
        ERR_BAD_TICK_SIZE = 71
        ERR_BAD_DAQO_CHAN_TYPE = 72
        ERR_NO_CONNECTION_ESTABLISHED = 73
        ERR_BAD_EVENT_TYPE = 74
        ERR_EVENT_ALREADY_ENABLED = 75
        ERR_BAD_EVENT_PARAMETER = 76
        ERR_BAD_CALLBACK_FUCNTION = 77
        ERR_BAD_MEM_ADDRESS = 78
        ERR_MEM_ACCESS_DENIED = 79
        ERR_DEV_UNAVAILABLE = 80
        ERR_BAD_RETRIG_TRIG_TYPE = 81
        ERR_BAD_DEV_VER = 82
        ERR_BAD_DIG_OPERATION = 83
        ERR_BAD_PORT_INDEX = 84
        ERR_OPEN_CONNECTION = 85
        ERR_DEV_NOT_READY = 86
        ERR_PACER_OVERRUN = 87
        ERR_BAD_TRIG_CHANNEL = 88
        ERR_BAD_TRIG_LEVEL = 89
        ERR_BAD_CHAN_ORDER = 90
        ERR_TEMP_OUT_OF_RANGE = 91
        ERR_TRIG_THRESHOLD_OUT_OF_RANGE = 92
        ERR_INCOMPATIBLE_FIRMWARE = 93
        ERR_BAD_NET_IFC = 94
        ERR_BAD_NET_HOST = 95
        ERR_BAD_NET_PORT = 96
        ERR_NET_IFC_UNAVAILABLE = 97
        ERR_NET_CONNECTION_FAILED = 98
        ERR_BAD_CONNECTION_CODE = 99
        ERR_CONNECTION_CODE_IGNORED = 100
        ERR_NET_DEV_IN_USE = 101
        ERR_BAD_NET_FRAME = 102
        ERR_NET_TIMEOUT = 103
        ERR_DATA_SOCKET_CONNECTION_FAILED = 104
        ERR_PORT_USED_FOR_ALARM = 105
        ERR_BIT_USED_FOR_ALARM = 106
        ERR_CMR_EXCEEDED = 107
        ERR_NET_BUFFER_OVERRUN = 108
        ERR_BAD_NET_BUFFER = 109

    class ScanStatus:
        """Scan status enumeration"""
        SS_IDLE = 0
        SS_RUNNING = 1

    # Types
    class DaqDeviceDescriptor(ctypes.Structure):
        """A structure that defines a particular LPAMS device."""
        _fields_ = [
            ("productName", c_char * 64),
            ("productId", c_uint),
            ("devInterface", c_int),
            ("devString", c_char * 64),
            ("uniqueId", c_char * 64),
            ("reserved", c_char * 512),
        ]

    class TransferStatus(ctypes.Structure):
        """A structure containing information about the progress of a scan operation."""
        _fields_ = [
            ("currentScanCount", ctypes.c_ulonglong),
            ("currentTotalCount", ctypes.c_ulonglong),
            ("currentIndex", ctypes.c_longlong),
            ("reserved", c_char * 64),
        ]

    # Rename types as per the SDK
    LPAMSDeviceDescriptor = DaqDeviceDescriptor
    LPAMSDeviceHandle = c_longlong
    LPAMSError = UlError

    # Function getters with proper error handling
    def _get_function(func_name, arg_types=None, restype=c_int):
        """
        Get a function from the LPAMSDK DLL, handling errors gracefully.
        """
        try:
            func = getattr(_lpamsdk, func_name)
            if arg_types:
                func.argtypes = arg_types
            func.restype = restype
            return func
        except AttributeError:
            print(f"Warning: Function '{func_name}' not found in LPAMSDK DLL")
            _functions_available = False
            return None

    # Try to get all the functions
    lpAMSGetDeviceInventory = _get_function(
        "lpAMSGetDeviceInventory",
        [POINTER(LPAMSDeviceDescriptor), POINTER(c_uint)]
    )
    
    lpAMSCreateDevice = _get_function(
        "lpAMSCreateDevice",
        [LPAMSDeviceDescriptor],
        restype=LPAMSDeviceHandle
    )
    
    lpConnectAMSDevice = _get_function(
        "lpConnectAMSDevice",
        [LPAMSDeviceHandle]
    )
    
    lpAMSAInGain = _get_function(
        "lpAMSAInGain",
        [LPAMSDeviceHandle, c_int, c_int, c_int]
    )
    
    lpAMSAInReadGain = _get_function(
        "lpAMSAInReadGain",
        [LPAMSDeviceHandle, POINTER(c_int), POINTER(c_int), POINTER(c_int)]
    )
    
    lpAMSAInScan = _get_function(
        "lpAMSAInScan",
        [LPAMSDeviceHandle, POINTER(c_double)]
    )
    
    lpAMSAInScanStatus = _get_function(
        "lpAMSAInScanStatus",
        [LPAMSDeviceHandle, POINTER(c_int), POINTER(TransferStatus)]
    )
    
    lpAMSAInScanStop = _get_function(
        "lpAMSAInScanStop",
        [LPAMSDeviceHandle]
    )
    
    lpDisconnectAMSDevice = _get_function(
        "lpDisconnectAMSDevice",
        [LPAMSDeviceHandle]
    )
    
    lpReleaseAMSDevice = _get_function(
        "lpReleaseAMSDevice",
        [LPAMSDeviceHandle]
    )
    
    if not _functions_available:
        print("\nWarning: Some or all LPAMSDK functions not found in the DLL.")
        print("This could be due to:")
        print("1. The DLL not exporting the functions")
        print("2. Different naming convention (name mangling)")
        print("3. Incompatible 32-bit/64-bit versions")
        print("4. The DLL being a static library")
        print("\nPlease check the DLL documentation for the correct usage.")
    
    # Export all symbols
    __all__ = [
        "DaqDeviceInterface",
        "UlError",
        "ScanStatus",
        "LPAMSDeviceDescriptor",
        "TransferStatus",
        "LPAMSDeviceHandle",
        "LPAMSError",
        "lpAMSGetDeviceInventory",
        "lpAMSCreateDevice",
        "lpConnectAMSDevice",
        "lpAMSAInGain",
        "lpAMSAInReadGain",
        "lpAMSAInScan",
        "lpAMSAInScanStatus",
        "lpAMSAInScanStop",
        "lpDisconnectAMSDevice",
        "lpReleaseAMSDevice"
    ]
    
except Exception as e:
    print(f"Error initializing LPAMSDK: {e}")
    import traceback
    traceback.print_exc()
