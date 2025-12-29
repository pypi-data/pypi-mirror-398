from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="time-server-pkg",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="提供JSON-RPC接口的时间服务器，支持获取不同时区的当前时间",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/time-server-pkg",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
    ],
    keywords=["time-server", "json-rpc", "fastapi", "timezone"],
    python_requires=">=3.7",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "pytz>=2023.3",
    ],
    entry_points={
        "console_scripts": [
            "time-server=time_server_pkg.main:main",
        ],
    },
    package_data={
        "time_server_pkg": ["py.typed"],
    },
)
