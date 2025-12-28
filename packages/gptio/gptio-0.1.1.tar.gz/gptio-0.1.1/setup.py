from setuptools import setup

setup(
    name="gptio",               # your module name
    version="0.1.1",
    author="wirnty",
author_email="skedovichusjdj@gmail.com.com",
    description="A simple Python module to interact with ChatGPT via OpenAI API.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    py_modules=["gptio"],       # <-- points to your single .py file
    python_requires=">=3.12",
    install_requires=[
        "requests>=2.31.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers"
    ],
)