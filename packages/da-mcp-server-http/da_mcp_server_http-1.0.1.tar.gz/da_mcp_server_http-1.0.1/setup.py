from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("LICENSE", "r", encoding="utf-8") as fh:
    license_text = fh.read()

setup(
    name="da-mcp-server-http",
    version="1.0.1",
    author="DeepSea Accounting Team",
    author_email="jianglinming@gmail.com",
    description="晨舟财务会计软件 MCP (Model Context Protocol) 服务器 - HTTP流式版本",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitee.com/jlmpp/da_mcp_server",
    license="MIT",
    packages=find_packages(),
    py_modules=["server", "config", "logging_config"],
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
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastmcp==2.13.0.2",
        "pydantic==2.12.4",
        "requests==2.32.5",
        "diskcache==5.6.3",
        "cachetools==6.2.1",
        "exceptiongroup==1.3.0",
        "pathvalidate==3.3.1",
    ],
    extras_require={
        "dev": [
            "pyinstaller==6.16.0",
            "build>=0.8.0",
            "twine>=4.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "da-mcp-server=server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "*": ["*.json", "*.yaml", "*.yml", "*.txt", "*.md", "*.spec"],
    },
)