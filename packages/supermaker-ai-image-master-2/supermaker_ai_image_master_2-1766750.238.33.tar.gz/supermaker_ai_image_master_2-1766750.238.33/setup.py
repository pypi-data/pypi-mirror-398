from setuptools import setup, find_packages

setup(
    name="supermaker-ai-image-master-2",
    version="1766750.238.33",
    description="High-quality integration for https://supermaker.ai/image/",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="SuperMaker",
    url="https://supermaker.ai/image/",
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
