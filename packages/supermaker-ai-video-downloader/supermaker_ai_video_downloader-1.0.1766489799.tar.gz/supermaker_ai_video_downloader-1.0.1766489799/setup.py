from setuptools import setup, find_packages

setup(
    name="supermaker-ai-video-downloader",
    version="1.0.1766489799",
    description="Generate branded links and HTML anchors for https://supermaker.ai/video/",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="SuperMaker",
    url="https://supermaker.ai/video/",
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
