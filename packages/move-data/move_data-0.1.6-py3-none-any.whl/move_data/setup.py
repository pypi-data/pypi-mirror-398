from setuptools import setup, find_packages

setup(
    name="move-data",
    version="0.1.6",
    description="A Python package for moving data between Google Sheets, SharePoint, Google Cloud Storage, and Snowflake",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/move-data",
    packages=["move_data"],
    package_dir={"move_data": "."},
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "pandas>=1.3.0",
        "pygsheets>=2.0.0",
        "snowflake-connector-python>=2.7.0",
        "google-cloud-storage>=2.0.0",
        "chardet>=4.0.0",
        "openpyxl>=3.0.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

