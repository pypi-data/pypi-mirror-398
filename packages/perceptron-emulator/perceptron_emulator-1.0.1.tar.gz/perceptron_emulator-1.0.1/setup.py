from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="perceptron-emulator",
    version="1.0.1",
    author="Rex Ackermann",
    author_email="",
    description="A GUI-based physical perceptron emulator with custom hardware-style widgets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rexackermann/perceptron-emulator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "PyQt6>=6.0.0",
        "numpy>=1.20.0",
    ],
    entry_points={
        "console_scripts": [
            "perceptron-emulator=main:main",
        ],
    },
)
