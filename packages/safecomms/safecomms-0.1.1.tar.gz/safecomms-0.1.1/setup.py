from setuptools import setup, find_packages

setup(
    name="safecomms",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": ["pytest", "twine", "build"],
    },
    author="SafeComms",
    author_email="support@safecomms.dev",
    description="Official Python SDK for SafeComms API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/SafeComms/safecomms-python",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
