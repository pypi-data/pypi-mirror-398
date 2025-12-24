from setuptools import setup

setup(
    name="graphrecon",
    version="1.1.1",
    py_modules=["graphrecon"],
    install_requires=[
        "aiohttp>=3.9.0"
    ],
    entry_points={
        "console_scripts": [
            "graphrecon=graphrecon:main",
        ]
    },
    author="memirhan",
    description="Fast async GraphQL endpoint scanner",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.9",
)