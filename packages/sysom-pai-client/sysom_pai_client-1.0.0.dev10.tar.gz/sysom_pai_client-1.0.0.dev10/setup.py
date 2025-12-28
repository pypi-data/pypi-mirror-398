# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh.readlines()]

setup(
    name="sysom-pai-client",
    version="1.0.0-dev10",
    author="Your Name",
    author_email="your.email@example.com",
    description="SysOM PAI Client for job monitoring and diagnosis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'sysom-pai-client=sysom_pai_client.client:main',
        ],
    },
    package_data={
        'sysom_pai_client': ['*.proto'],
    },
    include_package_data=True,
)