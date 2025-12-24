"""
Setup configuration for btbricks package.

This package is designed for MicroPython environments. While it's distributed
via PyPI for reference and documentation, actual deployment to MicroPython
devices uses one of these methods:

1. **Using micropip (MicroPython's package manager):**
   On the MicroPython device:
   ```python
   import micropip
   await micropip.install("btbricks")
   ```

2. **Using mpremote (for ESP32, SPIKE, etc.):**
   ```bash
   mpremote cp -r btbricks :btbricks
   ```

3. **Manual upload via WebREPL or Thonny:**
   Copy the btbricks/ folder to the device's filesystem.

For development/documentation on regular Python, you can install normally:
```bash
pip install btbricks
```
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="btbricks",
    version="0.1.0",
    author="Anton Vanhoucke",
    author_email="anton@antonsmindstorms.com",
    description="A MicroPython Bluetooth library for remote controlling LEGO hubs via BLE",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/antonvh/btbricks",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: MicroPython",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "Environment :: Handhelds/PDA Devices",
    ],
    python_requires=">=3.7",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.20.0",
            "black>=23.0",
            "flake8>=5.0",
            "mypy>=1.0",
        ],
    },
    keywords="micropython bluetooth ble lego hub control",
    project_urls={
        "Bug Reports": "https://github.com/antonvh/btbricks/issues",
        "Source": "https://github.com/antonvh/btbricks",
        "Documentation": "https://btbricks.readthedocs.io",
    },
)
