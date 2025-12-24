from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tiramisu-framework",
    version="3.0.0",
    author="Jony Wolff",
    author_email="frameworktiramisu@gmail.com",
    description="RAO Multi-Agent Colaborativo - Sistema de Governanca de Decisoes em IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tiramisu-framework/tiramisu-framework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11,<3.13",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "langchain==0.2.16",
        "langchain-community==0.2.16",
        "langchain-core==0.2.38",
        "langchain-openai==0.1.23",
        "faiss-cpu==1.8.0",
        "openai==1.47.0",
        "python-dotenv>=1.0.0",
        "pydantic==2.8.2",
        "pydantic-settings>=2.0.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "tiramisu=tiramisu.cli.commands:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "tiramisu": ["config/*.yaml"],
    },
)
