from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pixgo",
    version="1.0.0",
    author="PixGo Python Client",
    description="Cliente Python para integração com a API de pagamentos PIX do PixGo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DevWand/pixgo-python",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    keywords="pixgo pix pagamentos api brasil payment",
    project_urls={
        "Documentation": "https://pixgo.org/api/v1/docs",
        "Source": "https://github.com/DevWand/pixgo-python",
        "Bug Tracker": "https://github.com/DevWand/pixgo-python/issues",
    },
)
