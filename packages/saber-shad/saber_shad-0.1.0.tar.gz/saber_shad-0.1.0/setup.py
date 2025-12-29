from setuptools import setup, find_packages

setup(
    name="saber-shad",
    version="0.1.0",
    description="Shad integration library",
    author="Mehdi",
    author_email="mehdimogdarapi@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests",
        "pycryptodome"
    ],
    license="MIT",
    python_requires=">=3.7",
)