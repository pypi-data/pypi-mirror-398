from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vexo",
    version="2025.12.34",
    author="Vexo Team",
    author_email="contact@vexo.dev",
    description="The simplest YouTube downloader (CLI + Python API)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vexo-team/vexo",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "yt-dlp>=2023.12.30",
    ],
    entry_points={
        "console_scripts": [
            "vexo=vexo.cli:main",
        ],
    },
)