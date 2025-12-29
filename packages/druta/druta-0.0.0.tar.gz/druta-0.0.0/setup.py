import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

"""
release checklist:
0. cleanup `rm -rf druta.egg-info build dist/`
1. update version on `setup.py`
4. commit changes and push
5. make release on PyPI. Run the following commands:
    5.1 `python3 setup.py sdist bdist_wheel`
    5.2 (optional) `python3 -m pip install --user --upgrade twine`
    5.3 `python3 -m twine upload dist/*`
6. git tag the release: `git tag vX.Y.Z` and `git push origin vX.Y.Z`
"""



setuptools.setup(
    name="druta",
    version="0.0.0",
    description="druta (द्रुत) - A fast video dataset format for PyTorch (for when storage isn't a problem)",
    author="mayukhdeb",
    author_email="mayukhmainak2000@gmail.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mayukhdeb/druta",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)