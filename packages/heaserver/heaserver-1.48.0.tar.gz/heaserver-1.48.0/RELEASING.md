# Releasing the HEA Server Framework

## Python project versioning
Use semantic versioning as described in
https://packaging.python.org/guides/distributing-packages-using-setuptools/#choosing-a-versioning-scheme. In addition,
while development is underway, the version should be the next version number suffixed by `.dev`.

## Uploading releases to PyPI
From the project's root directory:
1. For numbered releases, remove `.dev` from the version number in setup.py, tag it in git to indicate a release,
   and commit to version control. For snapshot releases, leave the `.dev` suffix. You can append a number onto `.dev` to
   denote a sequence of snapshot releases, like `dev0`, `dev1`, etc. Make the commit message `Version x.x.x.`, replacing
   `x.x.x` with the actual version number being released. Name the tag `heaserver-x.x.x`, replacing
   `x.x.x` with the actual version number being released.
2. Run `python -m build` or `pyproject-build` to create the artifacts (wheel and sdist).
3. You need to configure an API token for PyPI in `$HOME/.pypirc` as follows:
```
[distutils]
index-servers =
	pypi
	...

[pypi]
username = __token__
password = <API token>

...
```
4. Run `twine upload -r <repository> dist/*` to upload to PyPI, using the repository name from your `.pypirc` file.
5. If you just made a numbered release, increment the version number in setup.py, append `.dev` to it. If you are
   making a sequence of snapshot releases, remember to increment the number after `.dev`. Commit to version control
   with the commit message, `Next development iteration.`

