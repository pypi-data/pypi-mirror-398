"""
setup.py for ctplite package
"""

from setuptools import setup, find_packages
from pathlib import Path
import sys
import importlib.util

# 读取README文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 从version.py读取版本号
version_file = Path(__file__).parent / "ctplite" / "version.py"
spec = importlib.util.spec_from_file_location("version", version_file)
version_module = importlib.util.module_from_spec(spec)
sys.modules["version"] = version_module
spec.loader.exec_module(version_module)
version = version_module.__version__

# 同步更新 pyproject.toml 中的版本号（如果存在）
pyproject_file = Path(__file__).parent / "pyproject.toml"
if pyproject_file.exists():
    import re
    pyproject_content = pyproject_file.read_text(encoding="utf-8")
    # 更新 pyproject.toml 中的版本号
    updated_content = re.sub(
        r'^version\s*=\s*["\'][^"\']+["\']',
        f'version = "{version}"',
        pyproject_content,
        flags=re.MULTILINE
    )
    if updated_content != pyproject_content:
        pyproject_file.write_text(updated_content, encoding="utf-8")

setup(
    name="ctplite",
    version=version,
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
        "grpcio>=1.70.0",
        "grpcio-tools>=1.70.0",
        "protobuf>=5.29.5",
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

