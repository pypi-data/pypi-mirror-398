from setuptools import setup, find_packages

setup(
    name="jease",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],  # No dependencies
    python_requires=">=3.8",
    description="JEase - JSON made easy: chainable, safe, and beginner-friendly JSON manipulation in Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/VaibhavRawat27/jease",
    author="Vaibhav Rawat",
    author_email="rawatvaibhav27@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
