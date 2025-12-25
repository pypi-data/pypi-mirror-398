from setuptools import setup, find_packages

setup(
    name="fx-sdk",
    version="0.3.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "fx_sdk": ["abis/*.json"],
    },
    install_requires=[
        "web3>=6.0.0",
        "eth-account>=0.5.0",
        "eth-typing>=3.0.0",
        "eth-utils>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    author="Christopher Stampar (@cstampar)",
    author_email="cstampar@me.com",
    description="A Pythonic SDK for f(x) Protocol",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://fx.aladdin.club/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
