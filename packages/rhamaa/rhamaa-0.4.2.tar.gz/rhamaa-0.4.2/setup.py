from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rhamaa",
    version="0.4.2",
    description="CLI tools to accelerate Wagtail web development with RhamaaCMS.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="RhamaaCMS Team",
    author_email="firdaus@rhamaa.com",
    url="https://github.com/RhamaaCMS/RhamaaCLI",
    project_urls={
        "Bug Reports": "https://github.com/RhamaaCMS/RhamaaCLI/issues",
        "Source": "https://github.com/RhamaaCMS/RhamaaCLI",
        "Documentation": "https://github.com/RhamaaCMS/RhamaaCLI/wiki",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Content Management System",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Wagtail",
    ],
    keywords="wagtail django cms cli rhamaa code-generator",
    install_requires=[
        "click>=8.0.0",
        "rich>=12.0.0",
        "requests>=2.25.0",
        "gitpython>=3.1.0",
    ],
    extras_require={
        "cms": [
            "wagtail>=5.0",
        ],
        "cv": [
            "ultralytics>=8.0.0",
            "opencv-python>=4.8.0",
        ],
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "twine",
            "build",
        ],
    },
    entry_points={
        "console_scripts": [
            "rhamaa=rhamaa.cli:main"
        ]
    },
    python_requires=">=3.7",
    include_package_data=True,
    zip_safe=False,
)
