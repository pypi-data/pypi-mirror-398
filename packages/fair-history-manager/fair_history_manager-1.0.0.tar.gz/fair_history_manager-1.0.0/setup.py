from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 尝试读取requirements.txt，如果失败则使用默认依赖
requirements = []
try:
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8-sig") as fh:
            requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    else:
        requirements = ["redis>=4.5.0"]
except UnicodeDecodeError:
    # 如果编码失败，使用默认依赖
    requirements = ["redis>=4.5.0"]

setup(
    name="fair-history-manager",
    version="1.0.0",
    author="wxhelper-async Team",
    author_email="",
    description="A Redis-based fair allocation algorithm for LLM chat history management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/fair-history-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=24.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/your-username/fair-history-manager/issues",
        "Source": "https://github.com/your-username/fair-history-manager",
        "Documentation": "https://fair-history-manager.readthedocs.io/",
    },
)
