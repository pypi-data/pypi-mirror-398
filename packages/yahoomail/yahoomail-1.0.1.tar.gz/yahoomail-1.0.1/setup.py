from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="yahoomail",
    version="1.0.1", # Version incrémentée pour permettre la mise à jour
    author="anarchy223",
    description="A high-performance, async Yahoo Mail login automator.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anarchy223/yahoomail",
    packages=find_packages(),
    license="CC BY-NC-SA 4.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Free For Home Use",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.7',
    install_requires=[
        "httpx>=0.24.0",
        "h2>=4.1.0",
    ],
)