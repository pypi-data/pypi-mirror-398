from setuptools import setup, find_packages

setup(
    name="mcfo-neoncontract",
    version="1.0.0",
    description="Neon Contract Protocol Buffer definitions for Python",
    packages=find_packages(),
    install_requires=[
        "grpcio>=1.58.0",
        "grpcio-tools>=1.58.0",
        "protobuf>=4.24.0",
    ],
    python_requires=">=3.8",
)
