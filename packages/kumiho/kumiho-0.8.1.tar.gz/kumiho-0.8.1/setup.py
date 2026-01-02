from setuptools import setup, find_packages

setup(
    name="kumiho",
    version="0.8.1",
    packages=find_packages(),
    install_requires=[
        "grpcio>=1.63.0",
        "grpcio-tools>=1.63.0",
        "protobuf>=4.25.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.2.0",
        ],
    },
    description="Client library for the Kumiho asset management system.",
    license="Apache-2.0",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "kumiho-auth=kumiho.auth_cli:main",
        ]
    },
)