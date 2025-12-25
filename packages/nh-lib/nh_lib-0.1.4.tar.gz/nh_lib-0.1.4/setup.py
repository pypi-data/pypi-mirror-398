from setuptools import setup, find_packages

setup(
    name="nh_lib",
    version="0.1.4",
    author="BI Minor Hotels",
    author_email="b.intelligence@minor-hotels.com",
    description="Repository containing the Minor BI team's Python library, featuring features we use every day.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://https://github.com/nhbigithub/Python_Library",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires =[
        "pandas",
        "numpy",
        "pandas-gbq",
        "google-cloud-bigquery",
        "pyodbc",
        "openpyxl",
        "tqdm",
        "chardet",
        "gcsfs"
    ]
)
