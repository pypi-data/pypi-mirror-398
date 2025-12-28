from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="safebrowse",
    version="0.3.1",
    description="Python SDK for SafeBrowse - AI-powered browser security with prompt injection detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SafeBrowse",
    author_email="aadilsayed19@gmail.com",
    # url="https://gitlab.com/aadil11/ai_browser",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ai security prompt-injection llm browser agent rag sanitization",
    project_urls={
        "Documentation": "https://ai-browser-5d4p.onrender.com/docs",
        # "Source": "https://gitlab.com/aadil11/ai_browser",
        # "Issues": "https://gitlab.com/aadil11/ai_browser/-/issues",
        "Demo": "https://ai-browser-5d4p.onrender.com",
    },
)
