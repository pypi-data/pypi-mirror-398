from setuptools import setup, find_packages

setup(
    name="piedrilldown",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python package for creating Bar-of-Pie and Pie-of-Pie charts with drill-down visualizations",
    long_description=open("README.md").read() if __name__ == "__main__" else "",
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/piedrilldown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.7",
    install_requires=[
        "matplotlib>=3.0.0",
        "numpy>=1.15.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black",
            "flake8",
        ],
    },
    keywords="visualization, charts, pie chart, bar chart, drilldown, matplotlib",
)
