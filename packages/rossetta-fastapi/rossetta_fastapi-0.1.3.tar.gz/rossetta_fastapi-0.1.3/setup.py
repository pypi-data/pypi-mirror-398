from setuptools import setup
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rossetta-fastapi",
    version="0.1.3",
    description="Zero-config network request obfuscation middleware for FastAPI - protect your APIs from reverse engineering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rossetta API Team",
    author_email="",
    url="https://github.com/yiheinchai/rossetta-api",
    project_urls={
        "Bug Tracker": "https://github.com/yiheinchai/rossetta-api/issues",
        "Documentation": "https://github.com/yiheinchai/rossetta-api#readme",
        "Source Code": "https://github.com/yiheinchai/rossetta-api/tree/main/packages/rossetta-fastapi",
    },
    py_modules=["rossetta_fastapi"],
    install_requires=[
        "fastapi>=0.100.0",
        "cryptography>=41.0.0",
        "python-multipart>=0.0.6",
        "starlette>=0.27.0",
        "itsdangerous>=2.1.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: FastAPI",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    keywords="fastapi middleware encryption obfuscation security rossetta api-security aes-256 hmac endpoint-obfuscation",
    license="MIT",
)
