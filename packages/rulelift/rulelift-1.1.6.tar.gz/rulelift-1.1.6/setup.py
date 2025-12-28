from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rulelift",
    version="1.1.6",
    author="aialgorithm",
    author_email="aialgorithm@example.com",
    description="A tool for analyzing rule effectiveness in credit risk management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aialgorithm/rulelift",
    packages=find_packages(),
    package_data={
        'rulelift': ['data/*.csv'],
    },
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "pandas>=1.0.0,<=2.3.3",
        "numpy>=1.18.0,<=2.4.0",
        "scikit-learn>=0.24.0,<=1.8.0",
        "matplotlib>=3.3.0,<=3.10.8",
        "seaborn>=0.11.0,<=0.13.2",
        "networkx>=2.5.0,<=3.6.1",
        "graphviz>=0.16,<1.0.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)