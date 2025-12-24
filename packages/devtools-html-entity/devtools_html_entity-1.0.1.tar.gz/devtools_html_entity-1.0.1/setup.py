from setuptools import setup, find_packages

setup(
    name="devtools_html_entity",
    version="1.0.1",
    description="HTML entity reference",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/html-entity",
    project_urls={
        "Homepage": "https://devtools.at/tools/html-entity",
        "Repository": "https://github.com/devtools-at/html-entity",
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
