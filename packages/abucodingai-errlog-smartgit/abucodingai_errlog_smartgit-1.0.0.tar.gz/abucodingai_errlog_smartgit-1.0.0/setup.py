from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="abucodingai-errlog-smartgit",
    version="1.0.0",
    author="Abu Coding AI",
    author_email="abucodingai@example.com",
    description="errlog-smartgit - SmartGit Error Handler with detailed feedback",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abucodingai/errlog-smartgit-py",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "smartgit-err=errlog_smartgit.cli:main",
        ],
    },
    install_requires=[
        "abucodingai-smartgit>=1.0.0",
        "colorama>=0.4.4",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black>=22.0", "flake8>=4.0"],
    },
)
