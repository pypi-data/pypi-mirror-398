import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nasstat",
    version="0.1.3",                          
    author="Dariel Cruz Rodriguez",
    author_email="hello@dariel.us",
    description="A python wrapper of the United States Federal Aviation Authority's National Airspace System API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cruzdariel/nasstat",  
    packages=setuptools.find_packages(),       
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",   
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",                   
    install_requires=[
        "requests>=2.20.0",
        "pytz>=2023.3",
    ],
)