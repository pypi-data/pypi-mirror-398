"""
Legacy shim so existing workflows can still run `pip install .`.
All metadata now lives in pyproject.toml and is handled by hatchling.
"""
from setuptools import setup

if __name__ == "__main__":
    setup()