from setuptools import setup, find_packages
from pathlib import Path

this_dir = Path(__file__).parent
readme = (this_dir / "README.md").read_text(encoding="utf-8") if (this_dir / "README.md").exists() else "CLI tool for parsing MongoDB logs with filters and summary statistics"

setup(
    name="queryhound",
    version="0.7.3",
    description="CLI tool for parsing MongoDB logs with filters and summary statistics",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Dwayne McNab",
    author_email="",
    url="https://github.com/dmcna005/queryhound_qh",
    license="MIT",
    packages=find_packages(include=["queryhound", "queryhound.*"]),
    include_package_data=True,
    install_requires=["tabulate", "numpy", "pandas"],
    extras_require={
        'dev': ['pytest']
    },
    entry_points={
        'console_scripts': [
            'qh=queryhound.cli:run'
        ]
    },
    python_requires='>=3.8',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
    project_urls={
        "Source": "https://github.com/dmcna005/queryhound_qh",
        "Issues": "https://github.com/dmcna005/queryhound_qh/issues",
    },
)
