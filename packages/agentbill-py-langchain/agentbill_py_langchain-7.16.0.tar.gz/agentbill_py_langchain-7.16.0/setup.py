from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentbill-py-langchain",
    version="7.16.0",
    author="AgentBill",
    author_email="dominic@agentbill.io",
    description="LangChain callback handler for automatic usage tracking and billing with AgentBill",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Agent-Bill/langchain",
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
        "langchain>=0.1.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "openai": ["langchain-openai>=0.0.1"],
        "anthropic": ["langchain-anthropic>=0.0.1"],
    },
    keywords="langchain agentbill ai agent billing usage-tracking openai anthropic llm observability callbacks",
)
