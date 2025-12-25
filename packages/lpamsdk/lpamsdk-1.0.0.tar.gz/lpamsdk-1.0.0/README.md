# pyLPAMSDK

A Python wrapper for the LPAMSDK.

## Overview

This package provides a Python interface to the LPAMSDK for interacting with LPAMS devices. It wraps the C API using ctypes, making it easy to use the SDK functionality from Python.

## Installation

1. Clone or download this repository.
2. Install the package using pip:

```bash
pip install .
```

## Requirements

- Python 3.9 or higher
- Windows operating system (since the SDK uses DLLs)

## Usage

### Enumerations

- `DaqDeviceInterface`: Device interface types (USB_IFC, BLUETOOTH_IFC, ETHERNET_IFC, ANY_IFC).
- `LPAMSError`: Error codes returned by SDK functions.
- `ScanStatus`: Scan status (SS_IDLE, SS_RUNNING).

### Structures

- `LPAMSDeviceDescriptor`: Contains information about a particular LPAMS device.
- `TransferStatus`: Contains information about the progress of a scan operation.

## Troubleshooting

### DLL Loading Issues

If you encounter issues with DLL loading, make sure:

1. The DLL files are in the correct location (`dll/` directory).
2. All required dependencies (like libusb-1.0.dll) are present.
3. You're using a 64-bit Python interpreter if the DLL is 64-bit, and vice versa.

## License

MIT License
