from setuptools import find_packages, setup

setup(
    name="flask_chameleon",
    version="0.0.1",
    license="MIT",
    description="Flask extension to use Chameleon templates.",
    author="Jan Murre",
    author_email="jan.murre@catalyz.nl",
    url="http://github.com/jjmurre/flask-chameleon",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=["Chameleon"],
)
