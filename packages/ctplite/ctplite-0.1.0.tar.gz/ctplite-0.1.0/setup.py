"""
setup.py for ctplite package
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="ctplite",
    version="0.1.0",
    description="Python SDK for CTPLite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ctplite@163.com",
    author_email="ctplite@163.com",
    url="https://www.ctplite.com",
    packages=find_packages(),
    package_data={
        'ctplite': ['proto/*.py'],
    },
    python_requires=">=3.8",
    install_requires=[
        "grpcio>=1.60.0",
        "grpcio-tools>=1.60.0",
        "protobuf>=4.25.0",
        "requests>=2.31.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    include_package_data=True,
    zip_safe=False,
)

