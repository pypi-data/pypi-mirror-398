from setuptools import setup, find_packages

setup(
    name="devtools_text_repeater",
    version="1.0.1",
    description="Text repeater",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/text-repeater",
    project_urls={
        "Homepage": "https://devtools.at/tools/text-repeater",
        "Repository": "https://github.com/devtools-at/text-repeater",
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
