from setuptools import setup, find_packages
from pathlib import Path

ROOT = Path(__file__).parent

setup(
    name="fraudet",
    version="0.0.2",
    description="Fraud probability prediction using CatBoost with isotonic calibration",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Tony",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    package_data={
        "fraudet": [
            "assets/*.cbm",
            "assets/*.pkl",
            "assets/*.json",
        ]
    },
    install_requires=[
        "numpy>=1.23",
        "pandas>=2.0",
        "joblib>=1.2",
        "scikit-learn>=1.3",
        "catboost>=1.2",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
