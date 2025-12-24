from setuptools import setup, find_packages

setup(
    name="devtools_word_counter",
    version="1.0.1",
    description="Word and character counter",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/word-counter",
    project_urls={
        "Homepage": "https://devtools.at/tools/word-counter",
        "Repository": "https://github.com/devtools-at/word-counter",
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
