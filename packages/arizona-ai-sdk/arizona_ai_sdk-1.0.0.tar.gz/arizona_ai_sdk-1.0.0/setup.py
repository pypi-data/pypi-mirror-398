from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="arizona_ai_sdk",
    version="1.0.0",
    author="ArizonaAI",
    author_email="fakelag712@gmail.com",
    description="Python SDK для ArizonaAI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Arizona-AI/arizona-ai-python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="arizonaai api sdk ai chat gpt",
    project_urls={
        "Documentation": "https://arizona-ai.ru/api-docs",
        "Source": "https://github.com/Arizona-AI/arizona-ai-python-sdk",
    },
)
