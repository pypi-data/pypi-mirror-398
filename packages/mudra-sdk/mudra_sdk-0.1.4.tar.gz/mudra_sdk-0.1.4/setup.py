from setuptools import setup, find_packages
from pathlib import Path

# Get the base directory
base_dir = Path(__file__).parent

# Read the README file for the long description
readme_file = base_dir / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()

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
    name="mudra_sdk",
    version="0.1.4",  
    packages=find_packages(exclude=["test*", "tests*"]),
    install_requires=[
        "bleak>=0.21.0",
    ],
    include_package_data=True,
    package_data={
        "mudra_sdk": package_data,
    },
    author="Foad Khoury",
    description="Python SDK for Mudra with native library support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    project_urls={
        "Documentation": "https://wearable-devices.github.io/#welcome"
    },
    keywords="mudra sdk bluetooth ble hardware",
    classifiers=[
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
    ],
)