from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="paralegal",
    version="0.1.0",
    author="Your Company",
    author_email="support@yourcompany.com",
    description="Multi-tenant LLM observability powered by OpenLLMetry",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourcompany/paralegal",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
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
        "traceloop-sdk>=0.20.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
    ],
    keywords="llm observability tracing opentelemetry openai anthropic",
)
