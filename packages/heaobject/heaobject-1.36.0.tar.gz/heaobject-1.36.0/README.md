# HEA Object Library
[Research Informatics Shared Resource](https://risr.hci.utah.edu), [Huntsman Cancer Institute](https://healthcare.utah.edu/huntsmancancerinstitute/), Salt Lake City, UT

The HEA Object Library contains data and other classes that are passed into and out of HEA REST APIs.


## Version 1.36.0
* Optimized check for whether user is a super-admin. System users cannot be a super-admin, so do not do more resource-
  intensive checks. Similarly, document that system users have no group membership, so expensive database checks are
  not needed.
* Added heaobject.root.PermissionContext.is_system_user method.
* Added needs_encryption annotation to heaobject.object.AWSCredentials.session_token attribute.

## Version 1.35.0
* Type hints cleanup.
* Added encrypted attribute support.
* Added dependency to cryptography.

## Version 1.34.1
* Added missing constructor to heaobject.bucket.BucketCollaborators.

## Version 1.34.0
* Added "sensitive" metadata attribute for marking HEAObject attributes as potentially containing sensitive data.
* Added scrubber module with tools for scrubbing sensitive HEAObject attributes.
* Improved performance of get_attributes() method. Added has_attribute() method.
* heaobject.decorators.get_attribute_metadata now returns None instead of raising an exception when the requested
  attribute does not exist.
* New heaobject.decorators.DEFAULT_ATTRIBUTE_METADATA object.
* New heaobject.root.HEAObject.has_attribute method.
* Optimized attribute fetching.
* New heaobject.root.to_dict and to_json to match from_dict and from_json.
* Moved heaobject.root.mangled implementation to heaobject.util.

## Version 1.33.0
* Replaced heaobject.volume.Volume.credential_id and credential_type_name with credentials_id.

## Version 1.32.0
* Removed heaobject.folder.Item.get_mime_type() class method.
* Made heaobject.folder.mime_type property read-write, defaulting to application/octet-stream.

## Version 1.31.2
* Fixed CollaboratorAction constructor raising "name 'Person' is not defined" error.
* Added type checking to CollaboratorAction constructor.

## Version 1.31.1
* Changed remove_collaborators_from so that removing collaborators actually deletes collaborators with no account info.

## Version 1.31.0
* Removed heaobject.root.AbstractAssociation and subclass.
* Added heaobject.attribute.UniqueListAttribute.
* Reorganized heaobject.attribute.HEAAttribute class hierarchy.
* Added pre_hook and post_hook constructor parameters to the HEAAttribute class hierarchy to perform operations before
  and/or after setting an attribute.
* In heaobject.attribute module, replaced copier function parameters with copy_behavior, which uses copy.copy,
  copy.deepcopy, or no copy depending on its values.
* Added heaobject.attribute.sequence_contains function.
* Added collaborators attribute to the heaobject.organization.Organization class.
* Added account_id attribute to the heaobject.person.CollaboratorAction class.
* Clarified that HEAObjects should have a a reasonable __eq__ implementation based on object attributes, and
  AbstractHEAObject has a reasonable default implementation that should work in most cases.
* Bumped email-validator version to 2.3.0, and removed uses of deprecated ValidatedEmail.email in the test cases.

## Version 1.30.0
* Implemented validation of bucket names.
* Implemented fuller version of S3Version desktop object with more attributes.
* Altered AWSS3FolderFileTrashItem to extend AWSDesktopObject.

## Version 1.29.0
* Replaced mimetype detection library with pyxdg.
* Added parent_uris attribute to heaobject.trash.TrashItem.
* Fixed compatibility of AttributeMetadata and descriptors. The attribute_metadata decorator only ever worked with
  properties, and now the descriptors in the heaobject.attribute module's descriptors allow passing an
  AttributeMetadata argument to their constructors.

## Version 1.28.1
* Made heaobject.root.HEAObject.get_attribute_metadata return default metadata for instance variables rather than raise
  AttributeError.

## Version 1.28.0
* The heaobject.account.AWSAccount.new_credentials method now returns temporary credentials. While this is usually what
  you want, in AWS-specific contexts you can set the temporary attribute to False as needed.

## Version 1.27.1
* Now super admins are granted permission to change an object's ownership, not just the original owner.

## Version 1.27.0
* Refactored attribute permissions checking and heaobject.organization.Organization permissions checking.

## Version 1.26.4
* Fixed typing error in implementation of heaobject.root.is_system_user method. This change does not alter behavior.

## Version 1.26.3
* Grant super-admins only VIEWER permissions for "system" people.

## Version 1.26.2
* Fixed issue with heaobject.person.Group super_admin_default_permissions property.

## Version 1.26.1
* Made /*super-admin default super-admin permissions VIEWER only.

## Version 1.26.0
* Removed default super-admin permissions from settings, volumes, and credentials objects to address issues with
  matching up volumes and credentials and accounts, and to resolve apparent duplicate settings objects (which are
  actually just the settings objects for all the users, but it's confusing to look at).

## Version 1.25.0
* Backed out the new attributes in heaobject.registry.* from version 1.24.0.

## Version 1.24.0
* Introduced descriptors.
* Added delete_preflight and link_preflights attributes to heaobject.registry.Resource and
  heaobject.registry.Component, respectively.
* Changed use of word property/properties to attribute(s), since we're moving toward a hybrid future with both
  properties and descriptors, so no assumptions should be made about how an attribute is implemented.

## Version 1.23.0
* Made heaobject.root.DesktopObject.super_admin_default_permissions implementations non-final everywhere.
* Added heaobject.root.DesktopObject.get_owner_permissions class method to allow variation in the permissions that an
  object's owner gets (in particular, only heaobject.registry.Collection objects support object creation).
* Added heaobject.root.Permission.non_class_permissions class method.
* Added heaobject.root.NonCreatorSuperAdminDefaultPermissionsMixin class.

## Version 1.22.0
* Replaced heaobject.root.Permission.CHECK_DYNAMIC with a desktop object property,
  heaobject.root.DesktopObject.dynamic_permission_supported.
* Added has_any method to heaobject.root.Permission to simplify checking for whether the current user has any of
  those permissions for a given desktop object.
* Added /*super-admin administrator group to heaobject.group, and added a desktop object property,
  heaobject.root.DesktopObject.super_admin_default_permissions for what permissions the administrator has for an
  object by default. The default implementation returns the empty list. Many desktop object classes override the
  default implementation to return specific permissions.
* Altered heaobject.root.PermissionContext to use the new dynamic_permission_supported and
  super_admin_default_permissions properties.
* Added support for the in operator to the heaobject.root.PermissionGroup protocol and
  heaobject.root.DefaultPermissionGroup class.
* Added group_id_from method to heaobject.root.PermissionContext to convert from a group as represented by the
  heaobject.group module to a heaobject.person.Group id.
* Added the following properties to the heaobject.registry.Resource class: display_in_system_menu,
  display_in_user_menu, and collection_mime_type.
* Fixed heaobject.registry.Resource.manages_creators to accept a string "boolean" value and convert to a boolean.
* Make heaobject.registry.Collection.mime_type read-write.
* New heaobject.setterlogic module with reusable functions for implementing setters. The initial implementation
  supports lists and sets of strings.
* Documented heaobject.person.Person.group_ids.
* Made heaobject.person.Role.id, name, and role raise a ValueError when attempting to set them to the empty string.
* Removed redundant id property implementation in heaobject.person.Group.
* Clarified that the heaobject.person.Group.id and group are expected to have a one-to-one relationship.
* Documented heaobject.person.Group.display_name.
* Made heaobject.person.Group.group raise a ValueError when attemptingn to set it to the empty string.
* Added is_admin_group function to the heaobject.group module.
* Changed the heaobject.group.is_system_group function's parameter name from id_ to group.

## Version 1.21.1
* Addressed bug in determining whether a share applies to a permission context.

## Version 1.21.0
* Fixed regressions in heaobject.root.HEAObject.get_attributes() running under Python 3.10, and improved documentation
  of get_attributes() and related functions.
* Bumped mypy version and dealt with the resulting type checking errors.
* Set check_untyped_defs = True in mypi.ini and fixed resulting errors.
* Added get_groups method to heaobject.root.PermissionContext.
* Added creator_groups and collection_accessor_groups properties and related add/remove methods to
  heaobject.registry.Resource.
* Added is_collection_accessor method to heaobject.registry.Resource.
* Added resource_type_and_id methods to all AWSDesktopObject implementations.
* heaobject.root.PermissionContext is no longer generic.
* heaobject.root.PermissionAssignment now has group and basis attributes that represent group permissions.
* heaobject.root.PermissionAssignment has two new methods: applies_to and get_applicable_permissions.
* Added new regions to heaobject.aws.RegionLiteral.
* Added covariant version of heaobject.root.DesktopObjectTypeVar, called DesktopObjectTypeVar_cov.

## Version 1.20.2
* Make heaobject.trash.AWSS3FolderFileTrashItem not break if the actual_object_type_name is
  heaobject.folder.AWSS3Project.

## Version 1.20.1
* Remove collaborator_id field that mistaken put in folder.

## Version 1.20.0
* Added new field for context path for all SearchItem derived objects.
* Restructured inheritance pattern for AWSS3SearchItemInFolder.

## Version 1.19.0
* heaobject.aws.S3StorageClass has a new attribute, requires_restore, that is True or False depending on whether
  objects with that storage class must be restored prior to being retrieved. This is needed mainly because of the
  Glacier IR storage class, which is an archived storage class but does not require a restore.
* Fixed heaobject.data.AWSS3FileObject.retrievable having the wrong value when the object's storage class is Glacier
  IR.
* Automatically set heaobject.data.AWSS3FileObject.archive_detail_state to
  heaobject.aws.S3ArchiveDetailState.NOT_ARCHIVED when the object's storage_class is set to
  heaobject.data.S3StorageClass.GLACIER_IR.
* Set heaobject.data.AWSS3FileObject.storage_class to None if heaobject.data.AWSS3FileObject.archive_detail_state is
  set to something other than heaobject.aws.S3ArchiveDetailState.NOT_ARCHIVED when the storage class is an archived
  class but does not require a restore to make retrievable. AWS does not permit restoring an object that has the
  Glacier IR storage class.
* Bumped mimetype_description version to 0.1.1, which necessitated a small change to heaobject.mimetype to maintain
  backward compatibility. It has updated mimetype matching logic, which might result in changes to the reported
  mimetype of a desktop object.

## Version 1.18.0
* Created heaobject.aws.S3StorageClassDetailsMixin with attributes to distinguish archived from unarchived objects.
* Added heaobject.root.EnumWithDisplayName.
* Changed heaobject.aws.S3StorageClass enum to inherit from EnumWithDisplayName (no API change).

## Version 1.17.4
* Removed S3EventNameMixin using string literal for event name
* Added copy_old_to_new method to heaobject.activity.DesktopObjectAction to simplify activity handling code.

## Version 1.17.2
* Bug fix for the S3EventNameMixin

## Version 1.17.1
* Ensure desktop objects in heaobject.activity.* have timezone-aware datetimes.
* Updated the type hints for heaobject.util.to_date_or_datetime to ensure it returns a datetime when given a datetime
  argument.

## Version 1.17.0
* Rewrote the heaobject.storage module.
* Added multiple datetime-related utility functions to heaobject.util.
* Added to_bool, get_locale, raise_if_not_subclass, and type_name_to_type to heaobject.util.
* Added a Sentinal class to heaobject.util to distinguish between omitted and None keyword arguments.
* When setting any HEA object attribute with a timezone-naive datetime, the system timezone is now assumed and added to
  the datetime object.
* Refactored Credentials and AWSCredentials.

## Version 1.16.0
* New heaobject.activity.DesktopObjectSummaryView object.
* New heaobject.util.raise_if_none_or_empty_string and raise_if_empty_string functions.
* heaobject.root.is_heaobject_type and is_desktop_object_type now have an optional type_ property.

## Version 1.15.0
* New attributes for activities for path info, display name, and description.

## Version 1.14.0
* Added support for Python 3.12.

## Version 1.13.0.post1
* 1.13.0 inadvertently omitted the changes from 1.12.7.

## Version 1.13.0
* Pulled the AWSCredentials.expiration attribute up to Credentials.
* More flexible API for customizing attribute permissions calculation.
* Added Permission.SHARER to the ACCESSOR_PERMS list.
* Added lifespan attribute to the Credentials class, effectively pulling up the AWSCredentials.temporary attribute into something more generic.

## Version 1.12.7
* Adds the AWSS3SearchItemInFolder for package search result data.

## Version 1.12.0
* Switched to orjson for json formatting and parsing. Updated other dependencies.

## Version 1.11.0
* Removed HEAObject.get_all_attributes(). Document that an HEAObject's repr is expected to conform to
  eval(repr(obj)) == obj.

## Version 1.10.2
* Prevent duplicate group ids in Person objects.

## Version 1.10.1
* Prevent duplicate collaborator ids in Organization objects.

## Version 1.10.0
* Updated minimum version of yarl due to an issue with trailing slashes on URLs in some earlier versions.
* Added desktop object support for adding collaborators to organizations.

## Version 1.9.4
* Addressed more typing issues. Allow '' and None to be interoperable ways of expressing a root folder.

## Version 1.9.3
* Yanked.

## Version 1.9.2
* Type hint fixes.

## Version 1.9.1
* Ensure heaobject.keychain.AWSCredentials.has_expired() handles an expiration attribute with an offset-naive value.
* Added optional type parameter for heaobject.root.type_for_name and heaobject.root.desktop_object_type_for_name.
* Type hint fixes.

## Version 1.9.0
* Consistently store timestamps generated by the app with a timezone in UTC.
* The AWSCredentials role attribute setter now checks for a valid ARN.
* The AWSCredentials object now has an account_id attribute that returns the role ARN's account id.
* The heaobject.util module has a new now() function that returns the current datetime in the UTC timezone.
* Updated some docstrings.

## Version 1.8.1
* Updated AWS region list.

## Version 1.8.0
* Fixed type hints, necessitating some minor API changes.

## Version 1.7.0
* Raise a ValueError when trying to set the DesktopObject id attribute to the empty string, which causes problems
downstream (when constructing URLs etc).
* New async methods for querying a user's permissions for a desktop object and its attributes. New heaobject.root.PermissionContext and heaobject.root.ViewerPermissionContext classes for working with the new methods.
* New instance_id attribute which is for storing an id that is unique across all object types in an instance of HEA.
* Improved docstrings.
* Standardized representation of tags across HEA with heaobject.root.TagsMixin.
* requirements_dev.txt now sets a minimum version of setuptools to address a security vulnerability. Also updated to a newer version of build.
* Fixed unit test for credential expiration timestamp that was broken by a previous release.

## Version 1.6.4
* Credential's expiration type changed from str to datetime
* Added to AWS Credential the managed flag
* Removed in Registry the check for NONE_USER to bypass having to be in is_creator_user list

## Version 1.6.3
* Add to Person AccessToken object.

## Version 1.6.2
* Fixed heaobject.account.AWSAccount.new_credentials() not setting the credentials' role.

## Version 1.6.1
* For heaobject.organization.Organization, managers can now modify the manager and member lists.

## Version 1.6.0
* Replaced heaobject.keychain.AWSCredentials role_arn attribute with a role attribute on heaobject.keychain.Credentials objects.
* Added group_ids attribute to heaobject.person.Person.
* New attributes in heaobject.account.Account: file_system_type, file_system_name.
* New methods in heaobject.account.Account: get_role_to_assume(), and new_credentials().
* Added full_name attribute to Person that is mirrors display_name.
* Removed file_system_name parameter from queries of a registry Component's
resources.
* New heaobject.volume.Volume credential_type_name attribute.
* Added role_ids attribute to heaobject.person.Group.
* heaobject.user.is_system_user() now returns True for the system|credentialsmanager user.
* Changed heaobject.organization.Organization.accounts to account_ids, which is
a string, and removed the heaobject.account.AccountAssociation class.
* Removed AWS-specific attributes and methods from heaobject.organization.Organization.
* Docstring improvements.
* Better default type_display_name for heaobject.account.AccountView objects.
* Added group_type attribute to heaobject.person.Group.

## Version 1.5.1
* Ensure AWSS3FileObject's display_name attribute always has a non-None value.

## Version 1.5.0
* Added attribute-level permissions.
* Fixed bug in checking equality of AbstractAssociation objects.

## Version 1.4.0
* Added "deleted" attribute to the trash module's TrashItem class.
* Added Group class to the person module.

## Version 1.3.0
* Added type_display_name attribute to all HEA objects.

## Version 1.2.0
* Created AbstractAssociation base class for complex associations between desktop objects.
* Used it for the association between organizations and accounts, and volumes and accounts.

## Version 1.1.1
* Documented DesktopObject.get_permissions, and fixed an issue where it returned the CHECK_DYNAMIC permission (it)
should replace CHECK_DYNAMIC with any dynamically computed permissions).

## Version 1.1.0
* Added APIs for generating Person objects representing system users.
* Added system|aws user.
* Added source module with system source names (previously was only in heaserver).

## Version 1.0.2
* More performance improvements converting to/from a HEAObject and a dictionary.

## Version 1.0.1
* Performance improvements converting from a HEAObject to a dictionary.

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
* Python 3.10, 3.11, or 3.12: Download and install Python from https://www.python.org, and select the options to install
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

### Running unit tests
Run tests with the `pytest` command from the project root directory. To test the mime type detection capability, you
must use Linux and install the shared-mime-info package. On Windows, you can install Windows Subsystem for Linux (WSL)
and either test on WSL or set the XDG_DATA_HOME environment variable in your Windows Command Prompt or Powershell to
the /usr/share directory of your Linux environment, for example in Powershell:
`$Env:XDG_DATA_HOME = "\\wsl.localhost\Ubuntu\usr\share"`. If the XDG_DATA_HOME variable is not set, the mime type
detection tests are skipped.

### Packaging and releasing this project
See the [RELEASING.md](RELEASING.md) file for details.
