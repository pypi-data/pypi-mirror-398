from setuptools import setup, find_packages

setup(
    name="caxample",
    version="0.1.0",
    author="Younghwa Yang",
    author_email="yh9369@gmail.com",
    description="Example generator for cache testing. Example amplifier for marginal frequency and temporal locality.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/YangYounghwa/caxample",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "numpy>=2.2.6",
    ],
    extras_require={
        "test": [
            "pytest>=7.0",
            "numpy>=2.2.6",
        ],
        "dev": [
            "pytest>=7.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    license="MIT",
)
