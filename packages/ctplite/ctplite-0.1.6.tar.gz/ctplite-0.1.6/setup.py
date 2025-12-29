"""
setup.py for ctplite package
"""

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
from setuptools.command.bdist_wheel import bdist_wheel
from pathlib import Path
import sys
import subprocess
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


def generate_proto_before_build():
    """在构建前运行generate_proto.py脚本"""
    script_path = Path(__file__).parent / "generate_proto.py"
    if script_path.exists():
        print("=" * 60)
        print("正在生成protobuf文件...")
        print("=" * 60)
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=script_path.parent
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"生成protobuf文件失败 (返回码: {result.returncode})。"
                "请检查generate_proto.py脚本的输出以获取详细信息。"
            )
        print("=" * 60)
    else:
        print(f"警告: 未找到 generate_proto.py 脚本: {script_path}")


def ensure_proto_package_included(packages_list):
    """确保 ctplite.proto 包被包含在包列表中"""
    if 'ctplite.proto' not in packages_list:
        proto_dir = Path(__file__).parent / 'ctplite' / 'proto'
        if proto_dir.exists() and (proto_dir / '__init__.py').exists():
            packages_list.append('ctplite.proto')
    return packages_list


class BuildPyCommand(build_py):
    """自定义build_py命令，在构建前生成proto文件"""
    def run(self):
        generate_proto_before_build()
        # 重新发现包，确保包含新生成的 proto 包
        self.distribution.packages = ensure_proto_package_included(
            find_packages(exclude=["examples", "examples.*"])
        )
        super().run()


class SDistCommand(sdist):
    """自定义sdist命令，在打包前生成proto文件"""
    def run(self):
        generate_proto_before_build()
        # 重新发现包，确保包含新生成的 proto 包
        self.distribution.packages = ensure_proto_package_included(
            find_packages(exclude=["examples", "examples.*"])
        )
        super().run()


class BDistWheelCommand(bdist_wheel):
    """自定义bdist_wheel命令，在打包前生成proto文件"""
    def run(self):
        generate_proto_before_build()
        # 重新发现包，确保包含新生成的 proto 包
        self.distribution.packages = ensure_proto_package_included(
            find_packages(exclude=["examples", "examples.*"])
        )
        super().run()


# 发现所有包，确保包含 ctplite.proto
packages = ensure_proto_package_included(
    find_packages(exclude=["examples", "examples.*"])
)

setup(
    name="ctplite",
    version=version,
    description="Python SDK for CTPLite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ctplite@163.com",
    author_email="ctplite@163.com",
    url="https://www.ctplite.com",
    packages=packages,
    package_data={
        'ctplite': ['proto/*.py'],
    },
    python_requires=">=3.8",
    install_requires=[
        "grpcio>=1.70.0",
        "grpcio-tools>=1.70.0",
        "protobuf>=5.29.5",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
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
    cmdclass={
        'build_py': BuildPyCommand,
        'sdist': SDistCommand,
        'bdist_wheel': BDistWheelCommand,
    },
)

