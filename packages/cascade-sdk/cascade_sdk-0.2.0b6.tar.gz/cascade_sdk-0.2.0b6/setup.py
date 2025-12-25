"""
Setup configuration for cascade-sdk package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cascade-sdk",
    version="0.2.0b6",
    author="Cascade",
    description="Agent observability SDK for tracking AI agent execution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["examples*", "mock_agent*", "dashboard*", "backend*", "tests*", "test*"]),
    python_requires=">=3.8",
    install_requires=[
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-exporter-otlp>=1.20.0",
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cascade=cascade.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

