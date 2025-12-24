from setuptools import setup, find_packages

setup(
    name="seedphase",            # must be unique
    version="2.2.0",
    author="Your Name",
    description="Password-protected BIP39 seed phrase generator",
    packages=find_packages(),
    install_requires=["bip-utils"],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "seedphase=seedphase.cli:run"
        ]
    },
)
