from setuptools import setup, find_packages
import pathlib
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")
setup(
    name="bhh",
    version="0.5.0",
    packages=find_packages(),
    description="BHH",
    install_requires=[
        "requests>=2.0.0",
        "Pillow>=10.0.0",
    ],
    license="BHAP",
    license_files=["LICENSE.txt"],
    author="Aria",
    author_email="aria.karami94713@gmail.com",
    long_description=README,
    long_description_content_type="text/markdown",
)
