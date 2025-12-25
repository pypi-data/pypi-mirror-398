import os
import sys
import ctypes

# Set up the DLL path
dll_dir = os.path.join(os.path.dirname(__file__), "dll")
dll_path = os.path.join(dll_dir, "lpamsdk.dll")

# Print current Python architecture
print(f"Python architecture: {sys.maxsize > 2**32 and '64-bit' or '32-bit'}")

# Print DLL existence
print(f"DLL path: {dll_path}")
print(f"DLL exists: {os.path.exists(dll_path)}")

# Print libusb existence
libusb_path = os.path.join(dll_dir, "libusb-1.0.dll")
print(f"libusb path: {libusb_path}")
print(f"libusb exists: {os.path.exists(libusb_path)}")

# Add DLL directory to PATH
os.environ['PATH'] = dll_dir + os.pathsep + os.environ['PATH']
print(f"Updated PATH includes DLL directory: {dll_dir in os.environ['PATH']}")

# Try to load the DLL with detailed error information
try:
    print("\nTrying to load DLL with CDLL...")
    dll = ctypes.CDLL(dll_path)
    print("✓ DLL loaded successfully with CDLL")
except Exception as e:
    print(f"✗ Failed to load DLL with CDLL: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\nTrying to load DLL with WinDLL...")
    dll = ctypes.WinDLL(dll_path)
    print("✓ DLL loaded successfully with WinDLL")
except Exception as e:
    print(f"✗ Failed to load DLL with WinDLL: {e}")
    import traceback
    traceback.print_exc()
