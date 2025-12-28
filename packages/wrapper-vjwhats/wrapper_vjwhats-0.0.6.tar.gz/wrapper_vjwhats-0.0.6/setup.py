from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
setup(
    name="wrapper-vjwhats",
    license="MIT",
    version="0.0.6",
    author="Renan Rodrigues",
    author_email="renanrodrigues7110@gmail.com",
    description="Wrapper for vjwhats library to send messages and sent messages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Renan-RodriguesDEV/wrapper-vjwhats",
    packages=find_packages(),
    install_requires=["selenium>=4.39.0", "pyperclip>=1.11.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13.0",
)
