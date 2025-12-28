from setuptools import setup, find_packages
setup(
    name="bikerider",  # Change this to a unique name
    version="0.1",
    packages=find_packages(),
    install_requires=['pandas'],
    description="A simple Python helper package",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Abhi_456",
    author_email="sattaruvenkataabhilash@gmail.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
