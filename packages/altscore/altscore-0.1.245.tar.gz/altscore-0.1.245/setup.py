from setuptools import find_packages, setup

long_description = "Python SDK for AltScore"

setup(
    name="altscore",
    version="0.1.245",
    description="Python SDK for AltScore. It provides a simple interface to the AltScore API.",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/altscore/altscore-python",
    author="AltScore",
    author_email="developers@altscore.ai",
    license="MIT",
    entry_points={},
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "loguru",
        "click",
        "requests",
        "pydantic==1.10.13",
        "httpx",
        "stringcase",
        "python-decouple",
        "python-dateutil==2.8.2",
        "pyjwt",
        "fuzzywuzzy~=0.18.0",
        "python-Levenshtein<=0.26.1",
        "aiofiles==24.1.0",
        "pydantic[email]"
    ],
    extras_require={
        "dev": ["pytest>=7.0", "twine>=4.0.2", "pandas", "tabulate"],
        "data-tools": ["pandas", "tabulate"]
    },
    python_requires=">=3.8",
)
