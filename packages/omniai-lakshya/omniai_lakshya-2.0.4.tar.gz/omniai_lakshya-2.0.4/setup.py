from setuptools import setup, find_packages

setup(
    name="omniai-lakshya",
    version="2.0.4",
    author="Lakshya Gupta",
    author_email="lakshyagupta1040@gmail.com",
    description="OmniAI - Complete AutoML Pipeline with 52+ algorithms",
    packages=find_packages(include=['omniai', 'omniai.*']),
    install_requires=["pandas>=1.0", "numpy>=1.19"],
)
