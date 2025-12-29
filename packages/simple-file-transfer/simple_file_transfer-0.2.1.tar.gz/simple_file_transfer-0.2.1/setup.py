from setuptools import setup, find_packages

setup(
    name="simple-file-transfer",
    version="0.2.1",
    packages=find_packages(),
    install_requires=[
        "flask>=2.3.0",
        "click>=8.1.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "sft=sft.cli:cli",
            "sfts=sft.cli:cli",
        ],
    },
    python_requires=">=3.8",
    author="Simple File Transfer",
    description="A simple file transfer service for temporary file sharing",
    long_description=open("README.md").read() if __file__ else "",
    long_description_content_type="text/markdown",
)
