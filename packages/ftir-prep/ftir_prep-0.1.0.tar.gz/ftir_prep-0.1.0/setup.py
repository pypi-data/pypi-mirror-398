"""
Setup do Framework de Pré-processamento FTIR
"""

from setuptools import setup, find_packages
import os

# Lê o README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Framework de Pré-processamento FTIR"

setup(
    name="ftir-prep",
    version="0.1.0",
    author="Lucas Mendonça",
    author_email="lucas.mendonca@example.com",
    description="Framework modular para otimização de pipelines de pré-processamento FTIR",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/ftir-preprocessing-framework",
    project_urls={
        "Bug Tracker": "https://github.com/username/ftir-preprocessing-framework/issues",
        "Documentation": "https://github.com/username/ftir-preprocessing-framework/docs",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scikit-learn>=1.0.0",
        "optuna>=3.0.0",
        "rampy>=0.1.0",
        "PyWavelets>=1.9.0",
        "statsmodels>=0.13.0",
        "pandas>=1.3.0",
        "matplotlib>=3.5.0",
        "shap>=0.41.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "myst-parser>=0.17",
        ],
    },
    keywords="ftir, spectroscopy, preprocessing, machine-learning, optimization, bioinformatics",
    license="MIT",
    zip_safe=False,
) 