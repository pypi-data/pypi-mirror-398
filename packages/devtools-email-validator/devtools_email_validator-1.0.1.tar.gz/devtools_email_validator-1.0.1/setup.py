from setuptools import setup, find_packages

setup(
    name="devtools_email_validator",
    version="1.0.1",
    description="Email address validator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevTools.at",
    author_email="hello@devtools.at",
    url="https://devtools.at/tools/email-validator",
    project_urls={
        "Homepage": "https://devtools.at/tools/email-validator",
        "Repository": "https://github.com/devtools-at/email-validator",
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
