from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="golv",
    version="1.1.0",
    author="GOPU.inc",
    author_email="ceoseshell@gmail.com",
    description="SDK Python pour GoLV - Terminal sécurisé pour IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gopu-inc/GoLV-VM",
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
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pydantic>=1.10,<2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "ai": [
            "openai>=1.0.0",
            "langchain>=0.0.300",
        ]
    },
    entry_points={
        "console_scripts": [
            "golv=main_golv:main",
        ],
    },
)
