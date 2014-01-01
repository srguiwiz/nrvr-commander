#!/usr/bin/python

"""nrvr.util.networkinterface - Utilities regarding registering operating system users

Class provided by this module is RegisteringUser.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

from collections import namedtuple

class RegisteringUser(namedtuple("RegisteringUser",
                                 ["username", "pwd", "fullname", "organization"])):
    """A user who is being registered."""

    __slots__ = ()

    def __new__(cls, username, pwd=None, fullname=None, organization=None):
        """Create new user who is being registered.
        
        username
            username.
        
        pwd
            password.
            May be None or empty string.
        
        fullname
            full name.
            If None then default to a copy of username, with the first letter of each word capitalized.
        
        organization
            organization name.
            If None then default to fullname."""
        if fullname is None:
            fullname = " ".join([word.capitalize() for word in username.split()])
        if organization is None:
            organization = fullname
        return super(RegisteringUser, cls).__new__(cls, username=username, pwd=pwd, fullname=fullname, organization=organization)

if __name__ == "__main__":
    print RegisteringUser("joe")
    print RegisteringUser("joe", "secret")
    print RegisteringUser("joe", "secret", "Joe Doe")
    print RegisteringUser("joe", "secret", "Joe Doe", "not organized at all")
