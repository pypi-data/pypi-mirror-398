from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="recipes-sdk",
    version="0.3.0",
    author="christiaansann",
    author_email="",
    description="Python SDK for working with recipes from JSON files. Includes 4819+ validated recipes across breakfast, lunch, dinner, and snack categories.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/krstnvt/recipes-dataset",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    include_package_data=True,
    package_data={
        "recipes_sdk": ["*.json"],
    },
)
