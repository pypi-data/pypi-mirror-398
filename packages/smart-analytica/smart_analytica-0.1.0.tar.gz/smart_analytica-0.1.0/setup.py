from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smart_analytica",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="View Sigma Computing iframes directly from Python!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smart_analytica",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "ipython>=7.0.0",   # Required for Jupyter display
    ],
    include_package_data=True,
    package_data={
        "smart_analytica": ["templates/*.html"],
    },
)