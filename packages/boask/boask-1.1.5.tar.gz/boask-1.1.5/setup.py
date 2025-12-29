from setuptools import setup, find_packages

setup(
    name="boask",
    version="1.1.5",
    description="Pure Python website engine. Zero dependencies. Real JSX templates.",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="OXOP",
    author_email="minbartek41@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    license="MIT",
    keywords=["web", "minimal", "jsx", "python", "no-dependencies"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)