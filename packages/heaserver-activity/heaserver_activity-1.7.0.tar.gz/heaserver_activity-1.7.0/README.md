# HEA Server Activity Microservice
[Research Informatics Shared Resource](https://risr.hci.utah.edu), [Huntsman Cancer Institute](https://hci.utah.edu),
Salt Lake City, UT

The HEA Server Activity Microservice is A service for tracking activity in hea.


## Version 1.7.0
* Bumped heaserver version to 1.48.0.
* Added support for encrypted Mongo and RabbitMQ passwords.

## Version 1.6.0
* Bumped heaserver version to 1.45.1.
* New startup.py module to initialize logging before importing any third-party libraries.
* New optional -e/--env command-line argument for setting the runtime environment (development, staging, or
  production). Logging is now configured based on this setting, unless the older -l/--logging argument is provided. The
  default value is development.
* Logs are now scrubbed.
* Log files are now excluded from git.

## Version 1.5.2
* Also pass Authorization header when getting an organization's volumes.

## Version 1.5.1
* Pass user header to organizations microservice when getting an organization's volumes.

## Version 1.5.0
* Bumped heaserver version to 1.43.3.
* Can now query desktop object actions by organization_id.
* Fixed recently accessed object query logic so it returns any action with a matching old or new volume id, if
  volume_ids are provided as query parameters.

## Version 1.4.1
* Filter out recently accessed projects with a None display name, since there's nothing to do with them really.
* Bumped heaserver version to 1.37.1.

## Version 1.4.0
* Bumped heaserver version to 1.35.0.
* Use new sort logic from heaserver 1.35.
* Added sort-related query parameters to OpenAPI specs.
* Fixed some OpenAPI spec issues.

## Version 1.3.2
* Bumped heaserver version to 1.32.0.

## Version 1.3.1
* Bumped heaserver version to 1.30.1 to avoid a potential issue with erroneously assigning CREATOR privileges.

## Version 1.3.0
* Added group permissions support.

## Version 1.2.2
* Eliminated race condition when saving received desktop object actions.

## Version 1.2.1
* Eliminated harmless exception showing up in the logs.
* Ensure that activity timestamps do not have the wrong or no timezone.
* Addressed issue with recently accessed objects not returning in the correct sort order.

## Version 1.2.0
* Added Python 3.12 support.
* Added support for new Activity and RecentlyAccessedView attributes.
* Returns more activity fields.
* Improves reliability of getting recently accessed objects.
* New /desktopobjectsummaryviews endpoint.

## Version 1.1.1
* Returned DesktopObjectAction objects now have a type_display_name attribute.
* Returned RecentlyAccessView objects now have a type_display_name attribute, and the default display_name is now
  Untitled Recently Accessed View (rather than Untitled RecentlyAccessedView).

## Version 1.1.0
* Added query parameter for excluding desktop objects actions with certain codes from query results and the web socket.

## Version 1.0.3
* Improved performance.

## Version 1.0.2
* Actually send received desktop objects over any web socket connections.
* Paginate desktop object actions correctly.

## Version 1.0.1
Fixed a wrong method call generating strings to send to the message broker.

## Version 1
Initial release.

## Runtime requirements
* Python 3.10 or 3.11

## Development environment

### Build requirements
* Any development environment is fine.
* On Windows, you also will need:
    * Build Tools for Visual Studio 2019, found at https://visualstudio.microsoft.com/downloads/. Select the C++ tools.
    * git, found at https://git-scm.com/download/win.
* On Mac, Xcode or the command line developer tools is required, found in the Apple Store app.
* Python 3.10 or 3.11: Download and install Python 3.10 from https://www.python.org, and select the options to install
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

### Running integration tests
* Install Docker
* On Windows, install pywin32 version >= 223 from https://github.com/mhammond/pywin32/releases. In your venv, make sure that
`include-system-site-packages` is set to `true`.

### Trying out the APIs
This microservice has Swagger3/OpenAPI support so that you can quickly test the APIs in a web browser. Do the following:
* Install Docker, if it is not installed already.
* Run the `run-swaggerui.py` file in your terminal. This file contains some test objects that are loaded into a MongoDB
  Docker container.
* Go to `http://127.0.0.1:8080/docs` in your web browser.

Once `run-swaggerui.py` is running, you can also access the APIs via `curl` or other tool. For example, in Windows
PowerShell, execute:
```
Invoke-RestMethod -Uri http://localhost:8080/activity/ -Method GET -Headers @{'accept' = 'application/json'}`
```
In MacOS or Linux, the equivalent command is:
```
curl -X GET http://localhost:8080/activity/ -H 'accept: application/json'
```

### Packaging and releasing this project
See the [RELEASING.md](RELEASING.md) file for details.
