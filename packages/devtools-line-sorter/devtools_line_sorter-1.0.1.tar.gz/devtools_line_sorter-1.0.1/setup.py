from setuptools import setup, find_packages

setup(
    name="devtools_line_sorter",
    version="1.0.1",
    description="Line sorter",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/line-sorter",
    project_urls={
        "Homepage": "https://devtools.at/tools/line-sorter",
        "Repository": "https://github.com/devtools-at/line-sorter",
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
