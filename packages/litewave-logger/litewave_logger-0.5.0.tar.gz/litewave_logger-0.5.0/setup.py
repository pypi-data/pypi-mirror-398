from setuptools import setup, find_packages

setup(
    name="litewave_logger",
    version="0.5.0",
    description="A centralized logging module for Litewave services.",
    author="Litewave",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "starlette",
        "celery",
        "requests",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
