from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bifrost-ai",
    version="1.0.0",  
    author="BifrostAI",
    author_email="support@bifrost.ai",
    description="Unified Python SDK for multiple AI providers with automatic conversation management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bifrost-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "redis": [
            "redis>=5.0.0",
        ],
        "postgresql": [
            "psycopg2-binary>=2.9.0",
        ],
        "all": [
            "redis>=5.0.0",
            "psycopg2-binary>=2.9.0",
        ]
    }
)