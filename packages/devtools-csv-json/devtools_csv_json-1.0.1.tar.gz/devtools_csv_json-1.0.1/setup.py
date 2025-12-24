from setuptools import setup, find_packages

setup(
    name="devtools_csv_json",
    version="1.0.1",
    description="CSV to JSON converter",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/csv-json",
    project_urls={
        "Homepage": "https://devtools.at/tools/csv-json",
        "Repository": "https://github.com/devtools-at/csv-json",
    },
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
