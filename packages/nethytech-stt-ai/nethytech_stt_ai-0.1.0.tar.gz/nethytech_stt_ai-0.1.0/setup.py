from setuptools import setup, find_packages

setup(
    name="nethytech-stt-ai",
    version="0.1.0",
    author="Anurag Singh",
    author_email="anusin2255@gmail.com",
    description="Speech to Text Python package",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "selenium",
        "webdriver-manager",
    ],
    python_requires=">=3.8",
)
