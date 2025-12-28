from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pipelinescript",
    version="0.1.2",
    author="Idriss Bado",
    author_email="idrissbadoolivier@gmail.com",
    description="Human-readable ML pipeline language with DSL, debugging, and visualization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/idrissbado/PipelineScript",
    project_urls={
        "Bug Tracker": "https://github.com/idrissbado/PipelineScript/issues",
        "Documentation": "https://github.com/idrissbado/PipelineScript#readme",
        "Source Code": "https://github.com/idrissbado/PipelineScript",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Interpreters",
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
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.0.0",
    ],
    extras_require={
        "full": [
            "xgboost>=1.5.0",
            "matplotlib>=3.5.0",
        ],
        "xgboost": ["xgboost>=1.5.0"],
        "viz": ["matplotlib>=3.5.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pipelinescript=pipelinescript.__main__:main",
        ],
    },
    keywords=[
        "machine-learning",
        "dsl",
        "pipeline",
        "ml-pipeline",
        "debugging",
        "visualization",
        "sklearn",
        "xgboost",
        "domain-specific-language",
        "data-science",
        "automl",
    ],
)
