from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ilovetools",
    version="0.2.18",
    author="Ali Mehdi",
    author_email="ali.mehdi.dev579@gmail.com",
    description="A comprehensive Python utility library with modular tools for AI/ML, data processing, and daily programming needs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AliMehdi512/ilovetools",
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
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
    ],
    extras_require={
        "ai": [
            "openai>=1.0.0",
            "transformers>=4.30.0",
            "torch>=2.0.0",
            "sentence-transformers>=2.2.0",
        ],
        "image": [
            "Pillow>=10.0.0",
            "opencv-python>=4.8.0",
        ],
        "audio": [
            "librosa>=0.10.0",
            "soundfile>=0.12.0",
        ],
        "all": [
            "openai>=1.0.0",
            "transformers>=4.30.0",
            "torch>=2.0.0",
            "sentence-transformers>=2.2.0",
            "Pillow>=10.0.0",
            "opencv-python>=4.8.0",
            "librosa>=0.10.0",
            "soundfile>=0.12.0",
        ],
    },
    keywords="utilities, tools, ai, ml, data-processing, automation, python-library, neural-networks, attention-mechanism, self-attention, multi-head-attention, transformers, bert, gpt, positional-encoding",
    project_urls={
        "Bug Reports": "https://github.com/AliMehdi512/ilovetools/issues",
        "Source": "https://github.com/AliMehdi512/ilovetools",
    },
)
