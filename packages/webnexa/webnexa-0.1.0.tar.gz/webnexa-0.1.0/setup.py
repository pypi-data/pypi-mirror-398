from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="webnexa",
    version="0.1.0",
    author="Fardin Ibrahimi",
    author_email="fiafghan@gmail.com",
    description=(
        "A Python library for loading websites and asking questions using Hugging Face AI. "
        "Developed by Fardin Ibrahimi, Bachelor of Science in Computer Science and CEO of Humanoid Company. "
        "Humanoid Company specializes in developing AI applications and models that closely emulate human actions "
        "and decision-making approaches, with the mission statement 'Not Human, Beyond Human'. "
        "This library enables more accessible and innovative web interaction capabilities."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/webnexa",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "llama-index>=0.10.0",
        "llama-index-readers-web>=0.1.0",
        "requests>=2.31.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
