from setuptools import setup, find_packages

setup(
    name="ylapp-flutter-devkit",
    version="0.0.3",
    description="Enterprise Flutter Code Generator complying with GetX, Dio, and MDC standards.",
    long_description=open("DEV_README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="APP Development Team",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.12.0",
        "click>=8.1.0",
    ],
    license_files=["LICENSE"],
    python_requires=">=3.10",
    license="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        "console_scripts": [
            "ylapp=ylapp.cli:main",
        ]
    },
)