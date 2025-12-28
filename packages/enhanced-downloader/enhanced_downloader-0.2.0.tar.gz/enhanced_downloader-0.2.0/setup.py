from setuptools import setup, find_packages
import os

# 读取README.md内容
with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="enhanced_downloader",
    version="0.2.0",
    description="一个功能强大的增强型下载模块，支持多线程下载、断点续传和进度显示",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Stabvalue",
    author_email="stabvalue@outlook.com",
    url="https://github.com/Stabvalue/enhanced_downloader",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "tqdm>=4.60.0",
        "psutil>=5.0.0"
    ],
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
    ],
    python_requires='>=3.7',
    keywords="download multi-threading resume progress",
    project_urls={
        "Bug Reports": "https://github.com/Stabvalue/enhanced_downloader/issues",
        "Source": "https://github.com/Stabvalue/enhanced_downloader",
    },
)
