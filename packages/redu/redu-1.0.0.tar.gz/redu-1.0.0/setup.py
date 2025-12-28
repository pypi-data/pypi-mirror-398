from setuptools import setup, find_packages

setup(
    name="redu",
    version="1.0.0",
    author="Miloš Živanović",
    author_email="support@redu.cloud",
    description="Redu Cloud CLI",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://redu.cloud",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.7",
        "requests>=2.31.0",
        "cryptography>=42.0"
    ],
    entry_points={
        "console_scripts": [
            "redu=redu.cli:cli"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
