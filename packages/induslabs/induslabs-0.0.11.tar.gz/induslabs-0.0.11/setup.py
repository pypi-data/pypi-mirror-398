from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="induslabs",
    version="0.0.11",
    author="IndusLabs",
    author_email="support@induslabs.io",
    description="Python SDK for IndusLabs Voice API - Text-to-Speech and Speech-to-Text",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/INDUS-AI-DEV/induslabs-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
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
        "requests>=2.25.0",
        "aiohttp>=3.8.0",
        "websocket-client>=1.7.0",
        "numpy>=1.24.0",
        "soundfile>=0.12.1"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    keywords="tts stt speech-to-text text-to-speech voice-api audio transcription indian-languages",
    project_urls={
        "Bug Reports": "https://github.com/INDUS-AI-DEV/induslabs-python/issues",
        "Documentation": "https://docs.induslabs.io",
        "Source": "https://github.com/INDUS-AI-DEV/induslabs-python",
    },
)
