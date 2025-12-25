from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mlserve-sdk",
    version="0.3.7",
    description='Python SDK for access to MLServe.com services',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nikosga/mlserve-sdk/tree/main',
    author='Nick Gavriil',
    license='Apache-2.0',
    packages=find_packages(),
    install_requires=[
        "requests",
        "joblib",
        "matplotlib",
        "pandas",
        "numpy"
    ],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)