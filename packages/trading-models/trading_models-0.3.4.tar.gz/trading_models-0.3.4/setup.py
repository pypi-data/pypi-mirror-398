from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="trading-models",
    version="0.3.4",
    author="Ricky Ding",
    author_email="e0134117@u.nus.edu",
    description="MLP, CNN, Transformer models for time-series trading predictions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SerenaTradingResearch/trading-models",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().splitlines(),
    python_requires=">=3.8",
    license="MIT",
    keywords=[
        "trading models",
        "neural networks",
        "time-series",
        "MLP",
        "CNN",
        "Transformer",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
    ],
)
