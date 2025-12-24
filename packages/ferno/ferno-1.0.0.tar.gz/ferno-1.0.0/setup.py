from setuptools import setup

setup(
    name="ferno",
    version="1.0.0",
    scripts=["ferno.py"],
    install_requires=[
        "textual",
    ],
    entry_points={
        "console_scripts": [
            "ferno=ferno:main",
        ],
    },
)