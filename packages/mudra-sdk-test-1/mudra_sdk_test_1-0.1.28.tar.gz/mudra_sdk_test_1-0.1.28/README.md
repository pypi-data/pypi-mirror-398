# Mudra SDK Python

Python SDK for Mudra with native library support.

## Native Library Structure

The SDK includes platform-specific native libraries (`.dll`, `.so`, `.dylib`) organized in the following directory structure:

```
mudra_sdk/libs/
├── windows/
│   ├── x86/
│   │   └── MudraSDK.dll
│   └── x64/
│       └── MudraSDK.dll
├── linux/
│   ├── x86_64/
│   │   └── MudraSDK.so
│   └── arm/
│       └── MudraSDK.so
├── darwin/
│   ├── x86_64/
│   │   └── MudraSDK.dylib
│   └── arm64/
│       └── MudraSDK.dylib
└── android/  (optional)
    ├── arm/
    │   └── MudraSDK.so
    └── aarch64/
        └── MudraSDK.so
```

## Usage

### Basic Usage

```python
from mudra_sdk import Mudra

# Initialize the SDK (automatically loads the native library)
mudra = Mudra()

# Access the native library if needed
if mudra.native_lib:
    # Use ctypes to call functions from the native library
    # Example: result = mudra.native_lib.some_function()
    pass
```

### Manual Library Loading

```python
from mudra_sdk import load_library, get_platform_info

# Get platform information
platform_name, arch = get_platform_info()
print(f"Platform: {platform_name}, Architecture: {arch}")

# Load a specific library
lib = load_library('MudraSDK', 'MudraSDK')

# Use the library with ctypes
# Example: lib.some_function.argtypes = [ctypes.c_int]
#          result = lib.some_function(42)
```

## Installation

```bash
pip install mudra_sdk_test_1
```

## Building from Source

```bash
python setup.py sdist bdist_wheel
```

The native library files are automatically included in the package distribution.

## Platform Detection

The SDK automatically detects the platform and architecture:
- **Windows**: `windows/x86/` or `windows/x64/`
- **Linux**: `linux/x86_64/` or `linux/arm/`
- **macOS (Darwin)**: `darwin/x86_64/` or `darwin/arm64/`
- **Android**: `android/arm/` or `android/aarch64/`

## Notes

- All native library files (`.dll`, `.so`, `.dylib`) in `mudra_sdk/libs/` are tracked in git
- The library loader automatically selects the correct file based on the current platform
- If a library is not found, a `FileNotFoundError` will be raised with helpful information

