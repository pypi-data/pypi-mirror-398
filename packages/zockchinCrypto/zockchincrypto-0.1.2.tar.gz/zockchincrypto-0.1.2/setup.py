from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="zockchinCrypto",
    version="0.1.2",    
    author="zyad mahmoud saad", 
    author_email="zyadmahmoud3993@gmail.com",
    description="A Python library for various encryption algorithms including Fernet, Vigenère, Caesar, and Replacement ciphers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    packages=find_packages(include=["zockchinCrypto", "zockchinCrypto.*"]),
    
    install_requires=[
        "cryptography",
    ],
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
    ],
    python_requires='>=3.6',
)