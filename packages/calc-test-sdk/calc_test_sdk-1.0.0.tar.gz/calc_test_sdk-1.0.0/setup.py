from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="calc-test-sdk",
    version="1.0.0",
    author="Your Name",
    author_email="your_email@example.com",
    description="一个简单的加法运算SDK，用于测试PyPI发布",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/calc-test-sdk",
    packages=find_packages(),
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=2.0.0",
        "httpx>=0.23.0",
        "python-dotenv>=0.19.0",
        "pyyaml>=5.4.1",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
            "build",
            "twine",
        ],
    },
    package_data={
        "": ["*.yaml", "*.yml"],
    },
    include_package_data=True,
)