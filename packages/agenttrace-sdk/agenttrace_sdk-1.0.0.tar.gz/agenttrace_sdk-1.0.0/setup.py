from setuptools import setup, find_packages

setup(
    name="agenttrace",
    version="1.0.0",
    description="AgentTrace SDK - AI Agent Observability & Debugging",
    long_description=open("README_SDK.md").read() if __import__("os").path.exists("README_SDK.md") else "",
    long_description_content_type="text/markdown",
    author="AgentTrace Team",
    author_email="support@agenttrace.io",
    url="https://agenttrace.io",
    project_urls={
        "Documentation": "https://docs.agenttrace.io",
        "Bug Tracker": "https://github.com/agenttrace/sdk/issues",
    },
    packages=find_packages(include=["agenttrace_slim", "agenttrace_slim.*"]),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
        "langchain": ["langchain>=0.1.0"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Debuggers",
        "Topic :: System :: Monitoring",
    ],
    keywords="ai agent tracing debugging observability llm openai",
)
