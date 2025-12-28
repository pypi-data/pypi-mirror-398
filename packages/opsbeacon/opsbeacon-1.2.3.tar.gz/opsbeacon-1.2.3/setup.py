from setuptools import setup, find_packages

setup(
    name="opsbeacon",
    version="1.2.3",
    author="Cihan Sahin",
    author_email="cihan@opsbeacon.com",
    description="OpsBeacon python client library to interact with the OpsBeacon API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ob2ai/ob-python-sdk", 
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1"
    ],
    extras_require={
        "cli": ["python-dotenv>=1.1.0"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
