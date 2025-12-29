from setuptools import setup, find_packages
import os

setup(
    name="agenttrace-sdk",
    version="0.3.1",
    packages=find_packages(),
    install_requires=[
        "cloudpickle>=3.0.0",
        "supabase>=2.0.0",
        "keyring>=24.0.0",  # Encrypted token storage
        "requests>=2.25.0",  # API key auth
    ],
    extras_require={
        "dev": ["openai", "groq", "pydantic", "python-dotenv"],
        "langchain": ["langchain"],
        "all": ["openai", "groq", "pydantic", "langchain", "python-dotenv"],
    },
    entry_points={
        "console_scripts": [
            "agenttrace=agenttrace.cli:main",
        ],
    },
    author="AgentTrace Team",
    description="Time-Travel Debugging for AI Agents",
    python_requires=">=3.8",
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
)

