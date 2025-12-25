"""
Setup script for pyqt-template-app
Compatible with both setuptools and pip
"""
from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

setup(
    name="stdd",
    version="0.1.0",
    description="Universal template for PyQt6 + PyMySQL applications with role-based access control",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/std",
    packages=find_packages(),
    package_data={
        "std": ["*.sql", "*.md", "*.txt"],
        "std.examples": ["*.py", "*.md"],
    },
    include_package_data=True,
    install_requires=[
        "PyQt6>=6.6.0",
        "PyMySQL>=1.1.0",
    ],
    python_requires=">=3.8",
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
    ],
    keywords="pyqt6 pymysql template gui database role-based-access",
)

