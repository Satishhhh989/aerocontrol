from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aerocontrol",
    version="1.0.0",
    author="AeroControl Team",
    description="Hand gesture mouse control for Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "opencv-python>=4.8.0",
        "mediapipe>=0.10.0",
        "numpy>=1.24.0",
        "python-uinput>=0.11.2",
        "pyautogui>=0.9.54",
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "aerocontrol=main:main",
        ],
    },
)