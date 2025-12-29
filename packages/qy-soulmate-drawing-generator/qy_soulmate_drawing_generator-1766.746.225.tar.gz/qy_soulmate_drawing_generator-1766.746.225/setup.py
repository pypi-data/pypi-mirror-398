from setuptools import setup, find_packages

setup(
    name="qy-soulmate-drawing-generator",
    version="1766.746.225",
    description="Professional AI Soulmate Drawing Generation. Easily integrate high-quality AI artwork into your Python applications with https://supermaker.ai/image/ai-soulmate-drawing-generator",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="SuperMaker",
    url="https://supermaker.ai/image/ai-soulmate-drawing-generator",
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
