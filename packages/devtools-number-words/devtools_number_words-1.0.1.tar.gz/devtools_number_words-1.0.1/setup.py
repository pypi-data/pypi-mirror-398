from setuptools import setup, find_packages

setup(
    name="devtools_number_words",
    version="1.0.1",
    description="Number to words converter",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/number-to-words",
    project_urls={
        "Homepage": "https://devtools.at/tools/number-to-words",
        "Repository": "https://github.com/devtools-at/number-to-words",
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
