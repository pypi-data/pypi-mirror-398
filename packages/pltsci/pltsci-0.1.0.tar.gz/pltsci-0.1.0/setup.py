from setuptools import setup, find_packages

setup(
    name="pltsci",
    version="0.1.0",
    description="A utility library for matplotlib plotting configuration",
    author="Muxkin",
    author_email="muxkin@foxmail.com",
    packages=find_packages(),
    install_requires=[
        "matplotlib",
        "numpy",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    license="MIT",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="matplotlib plotting visualization",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers", 
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
)
