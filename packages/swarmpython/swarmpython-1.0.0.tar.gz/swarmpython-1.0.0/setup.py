from setuptools import setup, find_packages

setup(
    name="swarmpython",
    version="1.0.0",
    description="A lightweight swarm intelligence framework for Python models",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scikit-learn",
        "joblib"
    ],
    python_requires='>=3.12',
)