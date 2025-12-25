from setuptools import setup, find_packages

setup(
    name="dia-compliance-tool",
    version="0.1.1",
    author="Your Name",
    description="Digital India Act compliance checker with rule-based and LLM-based analysis",
    packages=find_packages(),
    install_requires=[
        "requests",
        "fastapi",
        "uvicorn",
        "beautifulsoup4",
        "pdfminer.six",
        "groq",
        "axe-selenium-python",
        "lxml",
        "pydantic",
        "playwright",
    ],
    python_requires=">=3.8",
)
