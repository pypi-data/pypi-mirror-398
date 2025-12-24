from setuptools import setup, find_packages

setup(
    name="devtools_qr",
    version="1.0.1",
    description="QR code generator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/qr-generator",
    project_urls={
        "Homepage": "https://devtools.at/tools/qr-generator",
        "Repository": "https://github.com/devtools-at/qr-generator",
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
