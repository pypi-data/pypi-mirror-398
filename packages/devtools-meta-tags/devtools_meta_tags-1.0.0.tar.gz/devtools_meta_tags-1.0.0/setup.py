from setuptools import setup, find_packages

setup(
    name="devtools_meta_tags",
    version="1.0.0",
    description="Meta tags generator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/meta-tags-generator",
    project_urls={
        "Homepage": "https://devtools.at/tools/meta-tags-generator",
        "Repository": "https://github.com/devtools-at/meta-tags-generator",
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
