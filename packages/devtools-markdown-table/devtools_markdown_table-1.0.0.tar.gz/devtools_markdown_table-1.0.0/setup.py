from setuptools import setup, find_packages

setup(
    name="devtools_markdown_table",
    version="1.0.0",
    description="Markdown table generator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/markdown-table",
    project_urls={
        "Homepage": "https://devtools.at/tools/markdown-table",
        "Repository": "https://github.com/devtools-at/markdown-table",
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
