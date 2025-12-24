from setuptools import setup, find_packages

setup(
    name="toastCE",
    version="0.1.0",
    description="A easy and simple way to make custom exceptions.",
    author="toasta (toastman32)",
    author_email="toastman32@toastreal.xyz",
    packages=find_packages(),
    install_requires=["inspect", "sys"],
    python_requires=">=3.7", 
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
