from setuptools import setup, find_packages
from pathlib import Path

# Читаем README для длинного описания
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="stdp",
    version="0.2.0",
    author="willalone",
    description="Hotel Management System - PyQt6-based hotel management application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/willalone/std",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "stdp=stdp.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "stdp": ["ui/*.ui"],
    },
)

