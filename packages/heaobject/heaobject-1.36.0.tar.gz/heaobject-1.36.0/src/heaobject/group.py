"""
Defines the following reserved groups for desktop objects, for use in the group attribute of its shares and invites:

NONE_GROUP: 'system|none' -- for objects that have no particular group-level permissions.
TEST_GROUP: 'system|test' -- for use in testing HEA.

Furthermore, all groups beginning with 'system|' are reserved for system use.

As for user-generated groups, the groups are paths with a / separator so as to create groupings of groups. At present
there are two broad categories of groups:
* Administrator groups: are prefixed with '/*'.
* Organization groups: are currently all other groups. They must begin with a / followed by a letter or
number. They signify membership in an organization at the collaborator, member, manager, or admin level.

The /*super-admin group is reserved for the overall administrators of the system. They have all permissions for the
following desktop objects:
* All objects of type heaobject.registry.Collection.
* All objects of type heaobject.registry.Component.
* All objects of type heaobject.registry.Property.
* All objects of type heaobject.settings.SettingsObject.
* All objects of type heaobject.person.Person.
* All objects of type heaobject.person.Group.
* All objects of type heaobject.organization.Organization.
* All objects of type heaobject.activity.Activity.
* All objects of type heaobject.volume.Volume.
* All objects of type heaobject.volume.Filesystem.
* All objects of type heaobject.keychain.Credential
"""

NONE_GROUP = 'system|none'
TEST_GROUP = 'system|test'
SUPERADMIN_GROUP = '/*super-admin'


def is_system_group(group: str) -> bool:
    """
    Returns whether the given string is a system group or not.

    :param group: The string to check.
    :return: True or False.
    """
    return group in (NONE_GROUP, TEST_GROUP)


def is_admin_group(group: str) -> bool:
    """
    Returns whether the given string is an admin group or not.

    :param group: The string to check.
    :return: True or False.
    """
    return group.startswith('/*')

