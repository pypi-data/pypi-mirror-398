from setuptools import setup, find_packages
from pathlib import Path

# Get the base directory
base_dir = Path(__file__).parent

# Find all library files
libs_dir = base_dir / "mudra_sdk" / "libs"
package_data = []

# Recursively find all .dll, .so, and .dylib files
if libs_dir.exists():
    for lib_file in libs_dir.rglob("*.dll"):
        rel_path = lib_file.relative_to(base_dir / "mudra_sdk")
        package_data.append(str(rel_path))
    for lib_file in libs_dir.rglob("*.so"):
        rel_path = lib_file.relative_to(base_dir / "mudra_sdk")
        package_data.append(str(rel_path))
    for lib_file in libs_dir.rglob("*.dylib"):
        rel_path = lib_file.relative_to(base_dir / "mudra_sdk")
        package_data.append(str(rel_path))

setup(
    name="mudra_sdk_test_1",
    version="0.1.28",  
    packages=find_packages(),
    install_requires=[
        "bleak>=0.21.0",
    ],
    include_package_data=True,
    package_data={
        "mudra_sdk": package_data,
    },
    author="Foad Khoury",
    description="Mudra SDK",
    python_requires=">=3.7",
)