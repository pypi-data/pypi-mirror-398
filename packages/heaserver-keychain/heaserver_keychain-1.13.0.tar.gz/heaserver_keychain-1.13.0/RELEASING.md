# Releasing HEA

## Releasing HEA Python projects

### Python project versioning
Use semantic versioning as described in 
https://packaging.python.org/guides/distributing-packages-using-setuptools/#choosing-a-versioning-scheme. In addition,
while development is underway, the version should be the next version number suffixed by `.dev`.

### Uploading releases to PyPI
From the project's root directory:
1. For numbered releases, remove `.dev` from the version number in setup.py, tag it in git to indicate a release, 
   and commit to version control. For snapshot releases, leave the `.dev` suffix. You can append a number onto `.dev` to 
   denote a sequence of snapshot releases, like `dev0`, `dev1`, etc. Make the commit message `Version x.x.x.`, replacing
   `x.x.x` with the actual version number being released. Name the tag `<project_slug>-x.x.x`, replacing `project_slug`
   with the gitlab project name (e.g., `heaserver-registry`), and replacing `x.x.x` with the 
   actual version number being released.
2. Run `python setup.py clean --all sdist bdist_wheel` to create the artifacts.
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

## Setting up a HEA microservice to run in Docker for the first time
The following assumes that there is a released version of the microservice on https://pypi.org:
* Create a directory in this project's root folder that is named the microservice's gitlab slug (for example, 
  heaserver-organizations).
* Create .dockerfile, docker-entrypoint.sh, and Dockerfile files, using the other microservice directories as a guide.
* Run `freeze-requirements` with two arguments: the microservice name, and the version number, for example, 
  `freeze-requirements heaserver-folders 1.0.0a17`. This command will generate the project's requirements.txt file.
* Add the project to the docker-compose.yml, using the entries for the other microservices as a guide.

## Updating the version of a HEA microservice to run in Docker
Just run `freeze-requirements` as described in the section above to update the `requirements.txt` file.
