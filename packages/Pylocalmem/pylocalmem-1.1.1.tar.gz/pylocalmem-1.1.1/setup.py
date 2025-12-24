import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="Pylocalmem",
    version="1.1.1",
    author="Chasss",
    description="A python package for local process data manipulation",
    long_description=long_description,
    long_description_content_type="text/markdown",  # ensures syntax highlighting works
    packages=setuptools.find_packages(),
    install_requires=[
        "keystone-engine",
    ]
)