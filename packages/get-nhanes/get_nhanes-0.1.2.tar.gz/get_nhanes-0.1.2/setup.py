from setuptools import setup, find_packages

setup(
    name="get_nhanes",
    version="0.1.2",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pandas",
        "numpy"
    ],
    author="wqlt",
    author_email="P2415627@mpu.edu.mo",
    description="A Python package for processing NHANES data",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type='text/markdown',
    url="https://github.com/wqlttt/getNhanes",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
