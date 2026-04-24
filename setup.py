from setuptools import setup, find_packages

setup(
    name="blog-generation-agent",
    version="1.0.0",
    description="AI Agent that automates end-to-end blog generation workflow",
    author="AI Engineer Intern",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "openai>=1.0.0",
        "anthropic>=0.8.0",
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4",
        "tiktoken>=0.5.1",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "lxml>=4.9.3",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "numpy>=1.24.0",
        "Pygments>=2.16.0",
        "markdown>=3.5.0",
    ],
    entry_points={
        "console_scripts": [
            "blog-agent=main:main",
        ],
    },
)
