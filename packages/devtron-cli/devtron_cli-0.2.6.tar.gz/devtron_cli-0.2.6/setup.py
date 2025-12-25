from setuptools import setup, find_packages

setup(
    name="devtron-cli",
    version="0.2.6",
    packages=find_packages(),
    install_requires=[
        "PyYAML>=6.0",
        "requests>=2.28.0",
        "click>=8.0.0",
        "jsonmerge>=1.9.2",
        "deepdiff>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "tron=tron.cli:main",
        ],
    },
    author="Devtron Devops",
    author_email="devops@devtron.ai",
    description="Automated infrastructure and application management tool for Devtron",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/devtron-labs/tron-cli",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
