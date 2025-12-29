from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

    setup(
        name="macos-trackpad-pressure",
        version="0.1.2",
        author="Inesh Tickoo",
        author_email="itickoo@owu.edu",
        description="A utility for developers and researchers to monitor, record, and export pressure data from the Force Touch trackpad on macOS. Provides a graphical interface for live visualization and CSV export of touch input pressure and haptic stage, enabling analysis and prototyping with Apple trackpads.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/9nesh/trackforce",
        packages=find_packages(),
        classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: Multimedia :: Graphics",
        "Environment :: MacOS X :: Cocoa",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="macos trackpad pressure force-touch pyobjc sensor multitouch touchpad force-click input-event haptic feedback apple macbook",
    python_requires=">=3.7",
    install_requires=[
        "pyobjc-framework-Cocoa>=9.0",
    ],
    entry_points={
        "console_scripts": [
            "trackpad-pressure=trackpad_pressure.__main__:main",
        ],
    },
)