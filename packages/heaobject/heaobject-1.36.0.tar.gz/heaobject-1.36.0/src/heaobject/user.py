"""
Defines the following reserved "system" users for desktop objects, for use as values of a desktop object's owner
attribute and the user attribute of its shares and invites:

NONE_USER: 'system|none' -- for use the value of a desktop object's owner attribute for objects that are not owned by any particular user.
ALL_USERS: 'system|all' -- for use in sharing a file with all users.
TEST_USER: 'system|test' -- for use in testing HEA.
SOURCE_USER: 'system|source' -- the desktop object's owner is determined by the object's source system and is not accessible to HEA.
AWS_USER: 'system|aws' -- for permissions given to the AWS account holder.
CREDENTIALS_MANAGER_USER: 'system|credentialsmanager' -- for use by the credentials manager system.

Furthermore, all users beginning with 'system|' are reserved for system use. System users cannot be members of groups.

The SYSTEM_USERS constant is a tuple of all defined system users. The is_system_user() function checks whether a given
user is a system user.
"""

NONE_USER = 'system|none'
ALL_USERS = 'system|all'
TEST_USER = 'system|test'
SOURCE_USER = 'system|source'
AWS_USER = 'system|aws'
CREDENTIALS_MANAGER_USER = 'system|credentialsmanager'


SYSTEM_USERS = (
    NONE_USER,
    ALL_USERS,
    TEST_USER,
    SOURCE_USER,
    AWS_USER,
    CREDENTIALS_MANAGER_USER
)


def is_system_user(id_: str) -> bool:
    """
    Returns whether the given ID is a system user or not.

    :param id_: The user ID to check.
    :return: True or False.
    """
    return id_ in SYSTEM_USERS
