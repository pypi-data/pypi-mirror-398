from setuptools import setup, find_packages

setup(
    name="eduhelper",
    version="1.0.0",
    author="Mani Eyvazi",
    author_email="manieyvazi83@yandex.ru",
    description="A beginner-friendly Python library for student grades, deadlines, and study planning",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)