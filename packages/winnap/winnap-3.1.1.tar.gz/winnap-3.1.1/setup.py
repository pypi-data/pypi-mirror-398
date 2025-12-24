from setuptools import setup, find_packages
import os

# อ่านไฟล์ README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="winnap",
    version="3.1.1",  # ⬅️ อัปเดทเวอร์ชันเป็น 3.1.0
    author="x2slynexis",
    description="Modern Tkinter UI Library with auto-start pages and elegant components",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: User Interfaces",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.7",
    install_requires=[
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0",
        "requests>=2.31.0",
    ],
    keywords="tkinter, customtkinter, ui, gui, modern-ui, desktop-app",
)