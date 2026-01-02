# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fastapi-databoard",
    version="0.1.0",
    author="Your Name",
    author_email="bittusinghtech@gmail.com",
    description="A database administration dashboard for FastAPI applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Bittu2903/fastapi-databoard",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.100.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "jinja2>=3.0.0",
    ],
    extras_require={
        "async": ["asyncpg>=0.27.0"],
        "postgres": ["psycopg2-binary>=2.9.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    include_package_data=True,
    package_data={
        "fastapi_databoard": [
            "templates/*.html",
            "static/*.css",
            "static/*.js",
        ],
    },
)