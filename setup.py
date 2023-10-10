from setuptools import setup

setup(
    install_require = [
        "logging",
        "async-timeout",
        "asyncio",
        "websockets",
        "requests",
        'importlib-metadata; python_version<"3.8"',
    ]
)