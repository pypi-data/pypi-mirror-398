from setuptools import setup, find_packages

setup(
    name="OAM_KIST",
    version="0.1.2",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "matplotlib",
        "scipy",
        "opencv-python",
    ],
    author="Youngjun Kim",
    description="Quantum information and technology using OAM states and SLM",
    python_requires=">=3.7",
)