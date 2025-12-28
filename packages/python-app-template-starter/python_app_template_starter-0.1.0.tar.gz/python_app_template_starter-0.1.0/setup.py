from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="python-app-template-starter",
    version="0.1.0",
    author="GabriOliv",
    description="A Python application template starter with pre-configured structure for building Python applications.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GabriOliv/python-app-template-starter",
    project_urls={
        "Bug Tracker": "https://github.com/GabriOliv/python-app-template-starter/issues",
        "Source Code": "https://github.com/GabriOliv/python-app-template-starter",
    },
    packages=find_packages(),
    install_requires=[
        "PyYAML>=6.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="template starter python application",
    python_requires=">=3.12",
    entry_points={
        "console_scripts": [
            "python-app-template-starter=python_app_template_starter.cli:main",
        ],
    },
    include_package_data=True,
)
