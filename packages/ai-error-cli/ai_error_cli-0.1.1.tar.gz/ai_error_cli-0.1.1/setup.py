from setuptools import setup, find_packages

setup(
    name="ai-error-cli",  
    version="0.1.1",
    description="CLI tool to explain Python runtime errors using AI",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Paraj Bhatasana",
    author_email="bhatasanaparaj@gmail.com",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pydantic",
        "fastapi",
        'pydantic'
    ],
    entry_points={
        "console_scripts": [
            "ai-run=ai_error_cli.cli:main",  
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
