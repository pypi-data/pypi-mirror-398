from setuptools import setup, find_packages

setup(
    name="rustpy2025",
    version="0.2.6",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "aiogram>=3.4.0",
        "aiosqlite>=0.17.0",
    ],
    entry_points={
        "console_scripts": [
            "rustpy=rustpy.cli:main",
        ]
    }
)
