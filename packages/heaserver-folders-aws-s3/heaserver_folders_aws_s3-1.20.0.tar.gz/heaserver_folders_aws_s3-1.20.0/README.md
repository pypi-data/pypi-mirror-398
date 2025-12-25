# HEA Server AWS S3 Bucket Folders Microservice
[Research Informatics Shared Resource](https://risr.hci.utah.edu), [Huntsman Cancer Institute](https://healthcare.utah.edu/huntsmancancerinstitute/),
Salt Lake City, UT

The HEA Server AWS S3 Bucket Folders Microservice manages folders in AWS S3 buckets.


## Version 1.20.0
* Bumped heaserver version to 1.48.0.
* Added support for encrypted RabbitMQ and MongoDB passwords.

## Version 1.19.0
* Improved performance of opening AWS S3 objects.
* Don't offer expedited restore for objects stored in Deep Archive because AWS doesn't support it.
* Bumped heaserver version to 1.44.1.
* New startup.py module to initialize logging before importing any third-party libraries.
* New optional -e/--env command-line argument for setting the runtime environment (development, staging, or
  production). Logging is now configured based on this setting, unless the older -l/--logging argument is provided. The
  default value is development.
* Logs are now scrubbed.
* Presigned URL's backing IAM User's Policy is now locked down to just GetObject and GetObjectVersion Actions

## Version 1.18.2
* Ensure the HTTP response status is 403 when creating an S3 object when the user lacks permission to do so.
* Ensure the HTTP response status is 403 when uploading an S3 object when the user lacks permission to do so.
* Clear the cache after successfully uploading a file to S3.
* Don't include Unarchive link for S3 objects in GLACIER_IR storage.
* Bumped heaserver version to 1.43.3.

## Version 1.18.1
* Set download headers earlier so they're actually included in the stream.
* Fixed typographical error in delete confirmation message.
* Use heaserver.service.util.to_http_date.

## Version 1.18.0
* Item mime_type attribute now contains the actual object's mime type.

## Version 1.17.4
* Presigned url now properly parses head_object response to determine if object is archived.

## Version 1.17.3
* Corrected error message when attempting to move an archived file.

## Version 1.17.2
* The microservice now correctly generates error desktop object actions when a move fails due to preflight validation.
* The cache is now invalidated correctly when making an old version of an object current and when deleting a version.

## Version 1.17.1
* We now refresh correctly after starting a restore when a file being refreshed is in the root of a bucket.
* When zipping an empty bucket, we now return an empty zip file rather than respond with 404 for consistency with
  similar situations for folders and projects elsewhere.
* Added hea-downloader rel value for file, folder, and project opener choice links.

## Version 1.17.0
* Bumped heaserver version.
* Only include the presigned URL link when getting retrievable files.
* Include hea-deleter link for versions when the user has DELETER permissions.
* Populate the new S3Version attributes
* Populate S3Version permissions.
* During move and rename preflight, check whether the user has permissions to delete versions.
* Populate permissions for trash items.

## Version 1.16.3
* Invalidate more of the cache after completing a copy. The target folder's cached value wasn't getting cleared.

## Version 1.16.2
* Bumped heaserver version to 1.39.1.

## Version 1.16.1
* Bumped heaserver version to 1.39.0.
* Prevented closing the OpenSearch client from also closing the Mongo client for fetching S3 object metadata.

## Version 1.16.0
* Bumped heaserver version to 1.38.0, with new mimetype detection.
* Added hea-parent links to trash items.

## Version 1.15.5
* Invalidate the cache after restoring an object.
* Do more thorough cache invalidation.

## Version 1.15.4
* Backed out change from 1.15.3 as it's unnecessary.
* Bumped heaserver version to 1.37.2 to address a Mongo client access-after-close problem.

## Version 1.15.3
* Bug fix, placed lock around async status id to ensure the status is globally unique.

## Version 1.15.2
* Fixed erronously generated desktop object actions during moves with unpopulated new/old_object_display_name and
  new/old_object_description attributes.
* In unarchive requests, wait until AWS indicates the restore has begun before returning a response.
* Bumped heaserver version to 1.37.0.
* Addressed error getting the Trash when a deleted folder or project is in the trash.

## Version 1.15.1
* Update trash code to use constants for error handling.
* Changed the restore api to elevate privileges using the standard mechanism.

## Version 1.15.0
* Trash now elevates permissions to be able to restore s3 objects.
* Trash will recover if it encounters 403 for bucket in account.

## Version 1.14.4
* Updated the text for deletion message for objects. For versioned buckets there is 7 day grace period.

## Version 1.14.3
* Fixed handling of mode query parameter for getting content.
* Moves now preserve version order.
* Bumped heaserver version to 1.36.2.

## Version 1.14.2
* Fail download of folders and projects with more than > 10GB of unarchived files.
* Allow getting content of the root folder so that users can download an entire bucket.

## Version 1.14.1
* Made the endpoint for getting an uploader form accept the root folder.
* Return an error message when a user attempts to generate a presigned URL for an object that is archived, or they
  attempt to generate presigned URLs for a folder of objects and all of them are archived.
* Return an error message when creating a folder and then creating a project with the same name.

## Version 1.14.0
* Handles aws delete events from Accounts removing from opensearch when no versions are left of the object.

## Version 1.13.1
* Moves into the root of a bucket now complete successfully.

## Version 1.13.0
* Fixed heaserver.awss3folders.awsservicelib.list_object_versions when listing folders and projects.
* Fixed moves so that all non-deleted versions are moved.
* Bumped heaserver version to 1.35.0.
* Fixed references to heaserver.service.aiohttp.parse_sort.

## Version 1.12.3
* Corrections to retrieving versions.

## Version 1.12.2
* Bumped heaserver version to 1.33.0 to correct a potential issue causing the microservice to fail to send messages to
  RabbitMQ.

## Version 1.12.1
* Bumped heaserver version to 1.32.2 to correct a potential issue causing the microservice to fail to send messages to
  the message broker.

## Version 1.12.0
* Bumped heaserver version to 1.32.0.
* Added delete prefetch endpoints and corresponding links and form templates.

## Version 1.11.0
* We now mark folders and projects with the new hea-container, hea-self-container, and hea-actual-container rel values.

## Version 1.10.1
* Bumped heaserver version to 1.30.1.

## Version 1.10.0
* Added support for group permissions.

## Version 1.9.12
* Populate trash items with the correct type for projects and the correct type_display_name.

## Version 1.9.11
* Upgraded heaserver dependency; new boto3 version with common runtime enabled.

## Version 1.9.10
* Upgraded heaserver dependency for bug fix getting temporary AWS credentials.

## Version 1.9.9
* Made new object forms always read-write.

## Version 1.9.8
* Fixed logic for determining whether to include open, download, archive, and unarchive links.

## Version 1.9.7
* Ensure cache invalidation for deleted objects and their ancestor folders that do not correspond to S3 objects.

## Version 1.9.6
* Fixed a corner case where project metadata for a key with no corresponding S3 object was not marked as deleted.
* Fixed potential race conditions.
* Overwrite any pre-existing metadata when an S3 object has been created successfully.
* Fixed upload regression when uploading to the root of a bucket.

## Version 1.9.5
* Fixed error renaming a file by appending to the end of the filename, when the file has no extension.
* Projects restored from the trash no longer become regular folders.

## Version 1.9.4
* Ensure a self link is returned in the response to most GET calls.
* Filled in gaps in generating completely populated desktop object actions.
* We no longer generate open links for archived files because they are not openable.

## Version 1.9.3
* Moving folders and projects works more reliably, and moving now correctly errors out when an object in the same
  location already exists.
* Renaming an object to one with the same name now correctly fails with an error.

## Version 1.9.2
* Pass seconds not hours into the presigned URL request boto3 call, fixing issue with presigned URLs expiring
  almost immediately.

## Version 1.9.1
* Fixed hang when attempting to archive a folder or project containing already-archived objects.
* Fixed error when attempting to move a file.

## Version 1.9.0
* Moved storage endpoints into this microservice.
* New delete-all-items-in-bucket endpoint.
* Fixed presigned-URLs that expire before the requested expiration.

## Version 1.8.2
* Enhanced reliability of desktop object action generation.

## Version 1.8.1
* Fixed bug where copy fails if the target folder contains an object with a name that is a prefix of the object to be copied.
* Performance improvements.

## Version 1.8.0
* Added support for python 3.12.
* Improved performance of getting projects.

## Version 1.7.1
* Fixed regression causing move to fail.

## Version 1.7.0
* Removed integration tests that overlap with the unit tests.
* Accept the data query parameter for get requests for a speed boost.

## Version 1.6.1
* Dependency upgrades for compatibility with heaserver-keychain 1.5.0.
* Fixed wrong readOnly status for a trash item's size attribute in unit test.

## Version 1.6.0
* Make metadata follow objects during moves, copies, renames, and trash restores.
* Clear cache properly after deleting and restoring objects.
* Clear cache properly after moves, copies, and renames.
* Merged trash microservice.

## Version 1.5.6
* Fixed regression causing the service to crash when the user closes their browser in the middle of a download.

## Version 1.5.5
* Only resort to asynchronous get-items call when the call has taken longer than 30 seconds to come back.
* Use cache when retrieving file desktop objects.
* Fixed caching issue when moving a file from the root of a bucket.
* Reimplemented download to work with aiohttp 3.10.

## Version 1.5.4
* Fixed stale cache when converting a folder to a project.
* Permissions calculation speedup.
* Fixed stale cache when archiving a file.

## Version 1.5.3
* Fixed stale cache when copying a file to the root of a bucket.

## Version 1.5.2
* Fixed file renaming regression.

## Version 1.5.1
* Caching optimizations.

## Version 1.5.0
* Support mode and access_token query parameters when getting a file object.

## Version 1.4.1
* Improved permission denied messages.

## Version 1.4.0
* Present accurate file permissions.

## Version 1.3.0
* Merged the AWS S3 files microservice into this one.
* Fixed caching bugs affecting web client object explorer refresh.
* Avoid timeouts loading objects, which sporadically caused objects not to be returned.

## Version 1.2.2
* Prevent failed content downloads from hanging the microservice.

## Version 1.2.1
* Install setuptools first during installation.
* Correct issue where some users lost access to folder and folder items because the user lacked permissions in AWS to simulate permissions. Instead, such users will appear to receive full permission for everything, which was the behavior prior to version 1.2.0. As before, AWS will still reject requests that users lack permission for.

## Version 1.2.0
* Present accurate bucket permissions.

## Version 1.1.6
* Minor bug fixes.

## Version 1.1.5
* Made a project's unarchive restore duration required in the unarchive card.

## Version 1.1.4
* Made a folder's unarchive restore duration required in the unarchive card.

## Version 1.1.3
* Fixed potential issue preventing the service from updating temporary credentials.

## Version 1.1.2
* Fixed new folder form submission.

## Version 1.1.1
* Display type display name in properties card, and return the type display name from GET calls.

## Version 1.1.0
* Pass folder and project permissions back to clients.

## Version 1.0.13
* Changed presented bucket owner to system|aws.
* Omitted shares from the properties template.

## Version 1.0.12
* Improved upload desktop object action message.

## Version 1.0.11
* Improved performance.

## Version 1.0.10
* Support getting the content of a folder as a zip file when the folder has files > 2GiB in size.

## Version 1.0.9
* Prevent zip file corruption when getting the content of a folder.

## Version 1.0.8
* Addressed issue where downloads start failing for all users if one user interrupts their download.

## Version 1.0.7
* Addressed potential failures to connect to other CORE Browser microservices.

## Version 1.0.6
* Addressed potential exception while unarchiving objects.
* Addressed issue preventing copying and moving folders containing unarchived objects.
* Improved error message when attempting to copy or move a folder with archived objects.

## Version 1.0.5
* Improved validation for downloading objects and generating presigned URLs.

## Version 1.0.4
* Improved performance.
* Allow unarchived S3 objects to be downloaded.

## Version 1.0.3
* Fixed project downloading.

## Version 1.0.2
* Fixed project copy and move causing 404 error.

## Version 1.0.1
* Improved performance.
* Corrected issue copying, moving, and renaming folders and projects containing archived objects.
* Corrected error opening a project with an archived README.*.
* Skip archived objects when downloading a folder or project.

## Version 1
Initial release.

## Runtime requirements
* Python 3.10, 3.11, or 3.12.

## Development environment

### Build requirements
* Any development environment is fine.
* On Windows, you also will need:
    * Build Tools for Visual Studio 2019, found at https://visualstudio.microsoft.com/downloads/. Select the C++ tools.
    * git, found at https://git-scm.com/download/win.
* On Mac, Xcode or the command line developer tools is required, found in the Apple Store app.
* Python 3.10, 3.11, or 3.12: Download and install Python from https://www.python.org, and select the options to
install for all users and add Python to your environment variables. The install for all users option will help keep you
from accidentally installing packages into your Python installation's site-packages directory instead of to your
virtualenv environment, described below.
* Create a virtualenv environment using the `python -m venv <venv_directory>` command, substituting `<venv_directory>`
with the directory name of your virtual environment. Run `source <venv_directory>/bin/activate` (or `<venv_directory>/Scripts/activate` on Windows) to activate the virtual
environment. You will need to activate the virtualenv every time before starting work, or your IDE may be able to do
this for you automatically. **Note that PyCharm will do this for you, but you have to create a new Terminal panel
after you newly configure a project with your virtualenv.**
* From the project's root directory, and using the activated virtualenv, run `pip install wheel` followed by
  `pip install -r requirements_dev.txt`. **Do NOT run `python setup.py develop`. It will break your environment.**

### Running tests
Run tests with the `pytest` command from the project root directory. To improve performance, run tests in multiple
processes with `pytest -n auto`. If the XDG_DATA_HOME environment variable is populated, tests will assume the
presence of a working shared-mime-info installation, typically found in Linux distributions, with the
`./mime-db/mime/packages/application-x-bioformats.xml` file installed.

### Running integration tests
* Install Docker
* On Windows, install pywin32 version >= 223 from https://github.com/mhammond/pywin32/releases. In your venv, make sure that
`include-system-site-packages` is set to `true`.
* A compatible heaserver-registry Docker image must be available.
* Run tests with the `pytest integrationtests` command from the project root directory.

### Trying out the APIs
This microservice has Swagger3/OpenAPI support so that you can quickly test the APIs in a web browser. Do the following:
* Install Docker, if it is not installed already.
* Have a heaserver-registry docker image in your Docker cache. You can generate one using the Dockerfile in the
  heaserver-registry project.
* Run the `run-swaggerui.py` file in your terminal. This file contains some test objects that are loaded into a MongoDB
  Docker container.
* Go to http://127.0.0.1:8080/docs in your web browser.

Once `run-swaggerui.py` is running, you can also access the APIs via `curl` or other tool. For example, in Windows
PowerShell, execute:
```
Invoke-RestMethod -Uri http://localhost:8080/awss3folders/root/items -Method GET -Headers @{'accept' = 'application/json'}`
```
In MacOS or Linux, the equivalent command is:
```
curl -X GET http://localhost:8080/awss3folders/root/items -H 'accept: application/json'
```

### Packaging and releasing this project
See the [RELEASING.md](RELEASING.md) file for details.
