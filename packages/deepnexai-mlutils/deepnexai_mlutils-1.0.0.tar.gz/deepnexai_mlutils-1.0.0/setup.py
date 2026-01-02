from setuptools import setup, find_packages

setup(
    name="DeepNexAI_mlutils",
    version="1.0.0",
    description="TensorFlow model visualizer & dark summary generator",
    author="DeepNexAI",
    packages=find_packages(),
    install_requires=[
        "tensorflow",
        "pillow",
        "pydot",
        "graphviz"
    ],
    python_requires=">=3.8"
)
