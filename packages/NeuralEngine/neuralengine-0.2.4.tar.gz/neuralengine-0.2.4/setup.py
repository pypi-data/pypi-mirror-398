from setuptools import setup, find_packages


def read_readme():
    with open("README.md", "r", encoding="utf-8") as file:
        return file.read()
    
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as file:
        return file.read().splitlines()

setup(
    name="NeuralEngine",
    version="0.2.4",
    author="Prajjwal Pratap Shah",
    author_email="prajjwalpratapshah@outlook.com",
    maintainer="Prajjwal Pratap Shah",
    description="A framework/library for building and training neural networks.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Prajjwal2404/NeuralEngine",
    python_requires='>=3.10',
    install_requires=read_requirements(),
    packages=find_packages(),
    license="MIT with attribution clause",
    keywords="neural-networks, machine-learning, deep-learning, numpy, cupy, autograd",
    classifiers = [
    "Programming Language :: Python :: 3",
    "Operating System :: OS Independent"
    ]
)