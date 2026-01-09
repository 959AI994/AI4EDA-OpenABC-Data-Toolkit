from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai4eda-toolkit",
    version="0.1.0",
    author="AI4EDA Team",
    description="A comprehensive toolkit for EDA data processing and format conversion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/AI4EDA-OpenABC-Data-Toolkit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "networkx>=2.5",
        "torch>=1.8.0",
        "torch-geometric>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ai4eda=ai4eda.cli:main",
        ],
    },
    package_data={
        "": ["bin/*", "libs/*"],
    },
    include_package_data=True,
)
