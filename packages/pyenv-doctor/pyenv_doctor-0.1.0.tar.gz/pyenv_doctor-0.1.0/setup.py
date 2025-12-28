from setuptools import setup, find_packages

setup(
    name="pyenv-doctor",
    version="0.1.0",
    author="Ameer Roshan H",
    author_email="ameerroshan02@gmail.com",
    description="Diagnose Python environment issues and suggest fixes",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AMEER-ROSHAN/pyenv-doctor",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "packaging",
        "tomli; python_version < '3.11'",
    ],
    entry_points={
        "console_scripts": [
            "pyenv-doctor=pydoctor.cli:main",
        ]
    },
)
