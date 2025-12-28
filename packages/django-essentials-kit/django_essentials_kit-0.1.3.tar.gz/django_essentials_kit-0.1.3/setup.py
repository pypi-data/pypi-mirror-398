from setuptools import find_packages, setup

__version__ = "0.1.3"


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="django-essentials-kit",
    version=__version__,
    author="alex-deus",
    description="Essential utilities for Django development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alex-deus/django-essentials-kit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=3.2",
    ],
    keywords="django, utilities, admin, fancybox",
    project_urls={
        "Bug Reports": "https://github.com/alex-deus/django-essentials-kit/issues",
        "Source": "https://github.com/alex-deus/django-essentials-kit",
    },
)
