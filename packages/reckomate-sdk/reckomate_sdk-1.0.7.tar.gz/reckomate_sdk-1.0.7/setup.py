from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="reckomate-sdk",
    version="1.0.7",  # bumped after cleanup
    author="Reckomate AI",
    author_email="support@reckomate.com",
    description="Reckomate SDK - HTTP client & proxy layer for Reckomate backend APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/reckomate/reckomate-sdk",
    packages=find_packages(exclude=("tests*", "dist*", "build*")),
    include_package_data=True,

    package_data={
        "reckomate_sdk": [
            "services/*.py",
            "utils/*.py",
        ],
    },

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],

    python_requires=">=3.8",

    # 🔥 ONLY SDK RUNTIME DEPENDENCIES
    install_requires=[
        "httpx>=0.28.1",
        "typing-extensions>=4.8.0",
    ],

    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.12.0",
            "isort>=5.13.0",
            "mypy>=1.7.0",
            "build>=1.3.0",
            "twine>=4.0.2",
        ],
    },
)
