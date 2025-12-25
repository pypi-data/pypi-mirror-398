# HEA Person Microservice
[Research Informatics Shared Resource](https://risr.hci.utah.edu), [Huntsman Cancer Institute](https://hci.utah.edu),
Salt Lake City, UT

The HEA Person Microservice is A microservice designed to provide CRUD operations for the Person HEA object type.


## Version 1.11.0
* Bumped heaserver version to 1.48.0.
* Support added for encrypted Keycloak admin secret.
* Added log files to the .gitignore.

## Version 1.10.0
* Bumped heaserver version to 1.45.1.
* New startup.py module to initialize logging before importing any third-party libraries.
* New optional -e/--env command-line argument for setting the runtime environment (development, staging, or
  production). Logging is now configured based on this setting, unless the older -l/--logging argument is provided. The
  default value is development.
* Logs are now scrubbed.

## Version 1.9.6
* Don't generate collection run-time actions when retrieving all people.
* Fallback to the all-users cache when retrieving a single person and the data isn't in the user's cache, then pull
  from Keycloak.

## Version 1.9.5
* Fixed race conditions modifying groups.

## Version 1.9.4
* Fix for Keycloak 24.0.5 query param sent to instruct /Groups to return all SubGroups as well.

## Version 1.9.3
* Bumped heaserver version to 1.36.2. Changed rel values for system and user menu links so that specific icons show.

## Version 1.9.2
* Bumped heaobject version.
* Limit Person object permissions when the Person object represents the current user.

## Version 1.9.1
* Bumped heaserver version.
* Type checking cleanup.

## Version 1.9.0
* Bumped heaserver version to 1.30.1.
* The links for a heaobject.person.Person object now include links to any collection with a True value for its
  display_in_system_menu or display_in_user_menu attributes and the appropriate rel values for the system and user
  menus.
* Added missing type attributes to the user_shares and group_shares properties metadata.
* Removed heaobject.root.Permission.CREATOR from the permissions dropdown list metadata.
* New heaserver.person.keycloakmongo.PeopleServicePermissionContext that directly queries Keycloak rather than using
  the people service's REST APIs.
* Improved caching of group information retrieved from Keycloak.
* Don't attempt to fetch group information from Keycloak for system users.
* Implement retry when populating Keycloak for integration tests.

## Version 1.8.1
* Prevent attempting to change the group membership of system users.

## Version 1.8.0
* Support group permissions.

## Version 1.7.0
* Made endpoint for adding a user to a group not internal but restricted to the user themselves and
  system|credentialsmanager.

## Version 1.6.0
* /ping now attempts to connect to Keycloak and returns an error status code if Keycloak does not report itself
  healthy. Health checks must be enabled in Keycloak or /ping will respond with an error status code.

## Version 1.5.1
* Fixed potential hang when listing all people.
* Added python 3.12 support.

## Version 1.5.0
* Change credentials collection link to serve CredentialsView objects.
* Fixed missing AltHost property, and fixed logic for handling missing AltHost.

## Version 1.4.2
* Caching optimizations.

## Version 1.4.1
* Handle groups with arbitrarily long paths.

## Version 1.4.0
* Made system and user menus dynamic based on permissions in the heaserver-registry microservice.
* We now set finer-grained permissions when generating Person objects.
* Added multiple endpoints to support collaborator adding and removing from organizations.

## Version 1.3.4
* System menu now has shortcut to credentials

## Version 1.3.3
* Support more than 100 users.

## Version 1.3.2
* Adds ability got get access tokens internally for microservices.

## Version 1.3.1
* Prevent Volumes collection from appearing in the system menu.

## Version 1.3.0
* Display type display name in properties card, and return it from GET calls.
* Changed /groups and /roles to get all groups and roles.
* New API for modifying a person's groups.
* Fixed caching issue.
* Include system users in /people calls by default, but permit omitting them with the excludesystem query parameter.
* Group objects now have a group_type attribute to differentiate between ADMIN groups (starting with /*) and
ORGANIZATION groups (everything else, currently).
* Don't allow access to data modifying admin APIs unless you're the system|credentialsmanager, or the affected person
(for calls to add/remove groups to/from a person).

## Version 1.2.0
* Added /groups endpoint.
* Corrected 500 error with /roles endpoint in some circumstances.

## Version 1.1.0
* System users are now included in the people API calls.

## Version 1.0.7
* Improved performance.

## Version 1.0.6
* Added support for the new settings links in the web client.

## Version 1.0.5
* Added code for Organization system menu item, but commented it out for now.

## Version 1.0.4
* Improved performance.

## Version 1.0.3
* Fixed access token caching logic error.

## Version 1.0.2
* Get user's client-level roles correctly.

## Version 1.0.1
* Addressed intermittent 500 error when calling the Keycloak admin API.

## Version 1
Initial release.

## Runtime requirements
* Python 3.10, 3.11, or 3.12.
* A running Keycloak server, optionally with the health check API enabled on the same port as the other APIs. See
  https://www.keycloak.org/observability/health for details. Do not call the /ping endpoint if Keycloak's health check
  API is off.

## Development environment

### Build requirements
* Any development environment is fine.
* On Windows, you also will need:
    * Build Tools for Visual Studio 2019, found at https://visualstudio.microsoft.com/downloads/. Select the C++ tools.
    * git, found at https://git-scm.com/download/win.
* On Mac, Xcode or the command line developer tools is required, found in the Apple Store app.
* Python 3.10, 3.11, or 3.12: Download and install Python from https://www.python.org, and select the options to install
for all users and add Python to your environment variables. The install for all users option will help keep you from
accidentally installing packages into your Python installation's site-packages directory instead of to your virtualenv
environment, described below.
* Create a virtualenv environment using the `python -m venv <venv_directory>` command, substituting `<venv_directory>`
with the directory name of your virtual environment. Run `source <venv_directory>/bin/activate` (or `<venv_directory>/Scripts/activate` on Windows) to activate the virtual
environment. You will need to activate the virtualenv every time before starting work, or your IDE may be able to do
this for you automatically. **Note that PyCharm will do this for you, but you have to create a new Terminal panel
after you newly configure a project with your virtualenv.**
* From the project's root directory, and using the activated virtualenv, run `pip install -r requirements_dev.txt`.
**Do NOT run `python setup.py develop`. It will break your environment.**

### Trying out the APIs
This microservice has Swagger3/OpenAPI support so that you can quickly test the APIs in a web browser. Do the following:
* Install Docker, if it is not installed already.
* Run the `run-swaggerui.py` file in your terminal. This file contains some test objects that are loaded into a MongoDB
  Docker container.
* Go to `http://127.0.0.1:8080/docs` in your web browser.

Once `run-swaggerui.py` is running, you can also access the APIs via `curl` or other tool. For example, in Windows
PowerShell, execute:
```
Invoke-RestMethod -Uri http://localhost:8080/buckets/ -Method GET -Headers @{'accept' = 'application/json'}`
```
In MacOS or Linux, the equivalent command is:
```
curl -X GET http://localhost:8080/buckets/ -H 'accept: application/json'
```

### Running tests
Run tests with the `pytest` command from the project root directory. To improve performance, run tests in multiple
processes with `pytest -n auto`.

### Running integration tests
* Install Docker
* On Windows, install pywin32 version >= 223 from https://github.com/mhammond/pywin32/releases. In your venv, make sure that
`include-system-site-packages` is set to `true`.

### Packaging and releasing this project
See the [RELEASING.md](RELEASING.md) file for details.
