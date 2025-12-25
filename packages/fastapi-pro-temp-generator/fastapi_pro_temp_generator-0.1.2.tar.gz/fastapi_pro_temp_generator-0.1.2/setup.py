from setuptools import setup, find_packages

setup(
    name="fastapi-starter",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "fastapi-starter=fastapi_starter.main:main",
        ],
    },
)
