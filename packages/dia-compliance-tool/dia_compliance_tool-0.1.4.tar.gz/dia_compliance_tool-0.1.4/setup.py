from setuptools import setup, find_packages

setup(
    name="dia-compliance-tool",
    version="0.1.4",  # bump version
    author="Your Name",
    description="Digital India Act compliance checker with rule-based and LLM-based analysis",
    packages=find_packages(),
    python_requires=">=3.8",

    
    install_requires=[
        "requests>=2.0",
        "beautifulsoup4>=4.9",
        "lxml>=4.9",
        "pdfminer.six>=20221105",
        "groq>=0.4.2,<1.0",
        "pydantic>=2.9",
        "python-dotenv>=1.0.0",
    ],

    
    extras_require={
        "api": [
            "fastapi==0.104.1",
            "uvicorn==0.24.0",
            "python-multipart==0.0.6",
        ],
        "browser": [
            "playwright>=1.40",
            "axe-selenium-python",
        ],
        "ml": [
            "tensorflow==2.15.0",
            "tf-keras==2.15.0",
            "deepface==0.0.79",
        ],
        "all": [
            "fastapi==0.104.1",
            "uvicorn==0.24.0",
            "python-multipart==0.0.6",
            "playwright>=1.40",
            "axe-selenium-python",
            "tensorflow==2.15.0",
            "tf-keras==2.15.0",
            "deepface==0.0.79",
        ],
    },
)
