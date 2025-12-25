from setuptools import setup, find_packages
from pathlib import Path

this_dir = Path(__file__).parent
long_description = (this_dir / "README.md").read_text(encoding="utf-8")

setup(
    name="fitsearchcv",
    version="1.0.3",
    author="Swastik Verma",
    author_email="swastik.yash29052005@gmail.com",
    description="A smarter refit to sklearn.GridSearchCV and sklearn.RandomizedSearchCV to reduce over and underfitting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/heilswastik/FitSearchCV",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scikit-learn",
    ],
    python_requires=">=3.7",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
