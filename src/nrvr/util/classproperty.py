#!/usr/bin/python

"""nrvr.util.classproperty - Utility allowing class properties

Class provided by this module is classproperty."""

# see http://stackoverflow.com/questions/3203286/how-to-create-a-read-only-class-property-in-python
class classproperty(object):
    """A getter only @classproperty decorator."""
    def __init__(self, getter):
        self.getter = getter
    def __get__(self, instance, owner):
        return self.getter(owner)
