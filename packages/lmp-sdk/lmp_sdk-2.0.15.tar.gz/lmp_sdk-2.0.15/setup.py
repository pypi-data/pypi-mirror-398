from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lmp-sdk",
    version="2.0.15",
    author="LMP SDK Team",
    description="推理服务 Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lixiang/lmp-sdk-python",
    packages=find_packages(),
    package_dir={"": "."},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "lpai_asset>=2.3.38",
    ],
    dependency_links=[
        "https://artifactory.ep.chehejia.com/artifactory/api/pypi/liauto-pypi-l5/simple",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.900",
        ]
    }
)