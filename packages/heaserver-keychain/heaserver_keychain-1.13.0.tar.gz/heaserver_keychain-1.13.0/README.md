# HEA Keychain
[Research Informatics Shared Resource](https://risr.hci.utah.edu), [Huntsman Cancer Institute](https://hci.utah.edu),
Salt Lake City, UT

The HEA server Keychain is a service for managing laboratory and user credentials.


## Version 1.13.0
* Bumped heaserver version to 1.48.0.
* Support added for encrypted Mongo password.
* Support added for encrypting the heaobject.keychain.AWSCredentials session token in mongo.

## Version 1.12.1
* Bumped heaserver version to 1.47.2.
* Using the HEA_ENCRYPTION_KEY works again, although it's not recommended for use in production.

## Version 1.12.0
* Bumped heaserver version to 1.47.0.
* Supports EncryptionKeyFile configuration property.

## Version 1.11.0
* Bumped heaserver version to 1.46.0.
* Supports EncryptionKey configuration property, which causes heaobject.keychain.Credentials password attributes to be 
  encrypted in mongo.
* Supports the HEA_ENCRYPTION_KEY environment variable when building a docker image using this project's Dockerfile.
* Bumped mypy version to 1.16.1.

## Version 1.10.0
* Bumped heaserver version to 1.44.1.
* New startup.py module to initialize logging before importing any third-party libraries.
* New optional -e/--env command-line argument for setting the runtime environment (development, staging, or
  production). Logging is now configured based on this setting, unless the older -l/--logging argument is provided. The
  default value is development.
* Logs are now scrubbed.
* Presigned URL's backing IAM User's Policy is now locked down to just GetObject and GetObjectVersion Actions 

## Version 1.9.1
* Bumped heaserver verison to 1.43.3.
* Added missing asyncio.to_thread around boto3 calls.
* Improved error handling for old managed credentials cleanup coroutine.

## Version 1.9.0
* Bumped heaserver version to 1.43.0.
* New APIs for getting a CredentialsView object by id or by name.
* Documented APIs that require an Authorization header.

## Version 1.8.5
* Bumped heaserver version to 1.37.1 to address potential issue with the RabbitMQ connection failing.

## Version 1.8.4
* Bumped heaserver version to 1.33.0 to address potential issue where desktop object actions fail to be sent to 
  RabbitMQ.

## Version 1.8.3
* Bumped heaserver version to 1.32.2 to correct a potential issue causing the microservice to fail to send messages to
  the message broker.

## Version 1.8.2
* Bumped heaserver version to 1.32.1.
* The super_admin_default_permissions attribute is now an empty list.

## Version 1.8.1
* When detaching a managed user, ignore missing information.
* Addressed issue where created managed credentials objects do not appear immediately due to caching.
* Bumped heaserver version to 1.32.0.

## Version 1.8.0
* Bumped heaserver version to 1.30.1.
* Added missing type metadata for share objects in the properties metadata.
* Added super_admin_default_permissions property metadata to the properties metadata.
* Added tests for removal of CREATOR privileges.

## Version 1.7.0
* Added support for group permissions.

## Version 1.6.0
* Overhauled managed credentials endpoint.
* Added endpoint for creating credentials for presigned-URLs.

## Version 1.5.0
* Removed integration tests because they are too duplicative of the unit tests.
* Added /credentialsviews endpoint.
* Don't raise boto3 ClientError when trying to delete policies for a role that has already been deleted. There's a good chance the policies are gone too.

## Version 1.4.4
* Bug fix for Managed Credentials not being deleted after expiring.

## Version 1.4.3
* Caching optimizations.

## Version 1.4.2
* Display the role and shares properties again.

## Version 1.4.1
* Use the /credentials endpoint to delete the managed credential not /awscredentials.

## Version 1.4.0
* Fixed issue where credentials were inadvertently deleted.
* Made DELETE call for deleting managed AWS credentials more like other HEA microservices.

## Version 1.3.4
* Changes in naming of menu items for credentials and updated associated icons
* Generated Managed Credential's now outputs the expiration for users to copy to clipboard. 

## Version 1.3.3
* Making AWS Credential Username unique per account.

## Version 1.3.2
* Upgrading dependencies to get bug fixes affecting creating and deleting Managed Credentials.
* Increased delay of background task that checks to see if credentials are expired.

## Version 1.3.1
* Introduces Managed Credentials with ability create and specify life span of credential 

## Version 1.3.0
* Now all Credentials objects have a role attribute, replacing the old AWSCredentials role_arn attribute.

## Version 1.2.0
* Display type display name in properties card.

## Version 1.1.0
* Pass desktop object permissions back to clients.
* Return type_display_name attribute from GET calls.

## Version 1.0.3
* Improved performance.

## Version 1.0.2
* Added endpoint and links for generating an AWS CLI .aws/credentials file.

## Version 1.0.1
* Improved performance.

## Version 1
Initial release.

## Runtime requirements
* Python 3.10, 3.11, or 3.12

## Development environment

### Build requirements
* Any development environment is fine.
* On Windows, you also will need:
    * Build Tools for Visual Studio 2019, found at https://visualstudio.microsoft.com/downloads/. Select the C++ tools.
    * git, found at https://git-scm.com/download/win.
* On Mac, Xcode or the command line developer tools is required, found in the Apple Store app.
* Python 3.10, 3.11, or 3.12: Download and install Python 3.10 from https://www.python.org, and select the options to install 
for all users and add Python to your environment variables. The install for all users option will help keep you from 
accidentally installing packages into your Python installation's site-packages directory instead of to your virtualenv 
environment, described below.
* Create a virtualenv environment using the `python -m venv <venv_directory>` command, substituting `<venv_directory>`
with the directory name of your virtual environment. Run `source <venv_directory>/bin/activate` (or `<venv_directory>/Scripts/activate` on Windows) to activate the virtual
environment. You will need to activate the virtualenv every time before starting work, or your IDE may be able to do
this for you automatically. **Note that PyCharm will do this for you, but you have to create a new Terminal panel
after you newly configure a project with your virtualenv.**
* From the project's root directory, and using the activated virtualenv, run `pip install wheel` followed by
  `pip install -r requirements_dev.txt`. **Do NOT run `python setup.py develop`. It will break your environment.**

### Running tests
Run tests with the `pytest` command from the project root directory. To improve performance, run tests in multiple
processes with `pytest -n auto`.

### Versioning
Use semantic versioning as described in
https://packaging.python.org/guides/distributing-packages-using-setuptools/#choosing-a-versioning-scheme. In addition,
while development is underway, the version should be the next version number suffixed by `.dev`.

### Version tags in git
Version tags should follow the format `heaserver-keychains-<version>`, for example, `heaserver-keychains-1.0.0`.

### Uploading to an index server
The following instructions assume separate stable and staging indexes. Numbered releases, including alphas and betas, go
into the stable index. Snapshots of works in progress go into the staging index. Thus, use staging to upload numbered
releases, verify the uploaded packages, and then upload to stable.

From the project's root directory:
1. For numbered releases, remove `.dev` from the version number in setup.py, tag it in git to indicate a release,
and commit to version control. Skip this step for developer snapshot releases.
2. Run `python setup.py clean --all sdist bdist_wheel` to create the artifacts.
3. Run `twine upload -r <repository> dist/<wheel-filename> dist/<tarball-filename>` to upload to the
 repository. The repository name has to be defined in a twine configuration file such as `$HOME/.pypirc`.
4. For numbered releases, increment the version number in setup.py, append `.dev` to it, and commit to version
control with a commit message like, "Prepare for next development iteration."
