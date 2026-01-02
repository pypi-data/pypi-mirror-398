from setuptools import setup, find_packages
import platform
import os

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Common dependencies for all platforms
common_dependencies = [
    "dearpygui",
    "iso-639",
    "numpy",
    "scipy",
    "natsort",
    "psutil",
    "Pillow",
    "opencv-python",
    "libscrc",
    "tqdm",
    "qrcode",
    "python-barcode",
    "pydub",
    "pyzbar",
    "paho-mqtt",
    "requests",
    "pymata-aio",
    "PyQt5",
    "py-cpuinfo",
    "GPUtil",
    "matplotlib",
    "bitarray",
    "scikit-learn",
    "pyaudio",
    "pygments",
]

# Windows-specific dependencies
windows_dependencies = [
    "pywin32",
    "comtypes",
]

# Add platform-specific dependencies
if platform.system() == 'Windows':
    install_requires = common_dependencies + windows_dependencies
else:
    install_requires = common_dependencies

setup(
    name='damp11113',
    version='2025.2.22-1',
    license='MIT',
    author='damp11113',
    author_email='damp51252@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/damp11113/damp11113-library',
    description="A Utils library and Easy to using.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=install_requires,
)
