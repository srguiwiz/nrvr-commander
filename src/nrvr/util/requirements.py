#!/usr/bin/python

"""nrvr.util.requirements - Utilities for requirements for running script

Class provided by this module is SystemRequirements.

As implemented works in Linux.
As implemented requires which command.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2015.
Simplified BSD License"""

from nrvr.process.commandcapture import CommandCapture

class SystemRequirements(object):
    """Utilities regarding requirements on machine for running the script.
    
    As implemented requires which command."""
    
    @classmethod
    def which(cls, command):
        """Return path to command, or None if none found."""
        which = CommandCapture(["which", command],
                               copyToStdio=False,
                               exceptionIfNotZero=False, exceptionIfAnyStderr=False)
        if which.returncode == 0 and not which.stderr:
            return which.stdout.strip()
        else:
            return None

    # TODO consider allowing requiring minimum versions, maybe use distutils.version to compare
    @classmethod
    def commandsAvailable(cls, commands, listWhich=False):
        """Return allRequiredFound or a 2-tuple (allRequiredFound, whichCommandsFound).
        
        Default to return a boolean value whether all required commands have been found.
        
        Can return a 2-tuple with first item being a boolean value whether all required commands
        have been found, and second item being a list of which commands have been found.
        
        commands
            a list of strings, one for each command to be found.
            To allow alternatives, if instead of a string there is a tuple of sublists then
            whether for at least one sublist of the tuple all commands can be found.
        
        listWhich
            whether to return a 2-tuple (allRequiredFound, whichCommandsFound).
            Default only to return a boolean value allRequiredFound."""
        if not isinstance(commands, (list)):
            raise TypeError("class SystemRequirements method commandsAvailable expects commands parameter to be a list, not {0}".format(commands))
        anyRequiredNotFound = False
        whichCommandsFound = []
        for command in commands:
            if not command:
                # avoid dealing with empty string or tuple
                continue
            if isinstance(command, basestring):
                # require one command
                which = CommandCapture(["which", command],
                                       copyToStdio=False,
                                       exceptionIfNotZero=False, exceptionIfAnyStderr=False)
                whichCommand = which.stdout.strip()
                if which.returncode == 0 and not which.stderr:
                    # found this one
                    if not whichCommand in whichCommandsFound:
                        # keep a list
                        whichCommandsFound.append(whichCommand)
                else:
                    # one not found
                    anyRequiredNotFound = True
            elif isinstance(command, (tuple)):
                # a tuple means alternatives allowed
                alternatives = command
                # require at least one of several lists of commands
                oneAlternativeComplete = False
                for alternative in alternatives:
                    alternativeComplete, alternativeCommands = SystemRequirements.commandsAvailable(alternative,
                                                                                                    listWhich=listWhich)
                    if alternativeComplete:
                        # this one at least
                        oneAlternativeComplete = True
                    # keep a list
                    whichCommandsFound = list(set(whichCommandsFound + alternativeCommands))
                if not oneAlternativeComplete:
                    # one not found
                    anyRequiredNotFound = True
            else:
                raise TypeError("class SystemRequirements method commandsAvailable expects commands parameter to be a list of strings or tuples, not to contain {0}".format(command))
        if not listWhich:
            return not anyRequiredNotFound
        else:
            return not anyRequiredNotFound, whichCommandsFound

    @classmethod
    def commandsRequired(cls, commands, verbose=False):
        """Raise exception if a required command cannot be found.
        
        Return a list of which commands have been found.
        
        commands
            a list of strings, one for each required command.
            To allow alternatives, if instead of a string there is a tuple of sublists then
            for at least one sublist of the tuple all commands are required."""
        allRequiredFound, whichCommandsFound = SystemRequirements.commandsAvailable(commands,
                                                                                    listWhich=True)
        if verbose:
            print "found commands:"
            for whichCommand in whichCommandsFound:
                print whichCommand
        if not allRequiredFound:
            raise Exception("required commands including alternatives are {0} but only found {1}".format(commands,
                                                                                                         whichCommandsFound))
        return whichCommandsFound

    @classmethod
    def commandsRequiredByImplementations(cls, implementations, verbose=False):
        """Raise exception if a required command cannot be found.
        
        Return a list of which commands have been found."""
        commandsUsedInImplementations = []
        for implementation in implementations:
            methodCommandsRequired = getattr(implementation, "commandsUsedInImplementation", None)
            if callable(methodCommandsRequired):
                # one implementation
                commandsUsedInImplementations.extend(implementation.commandsUsedInImplementation())
            else:
                # apparently this implementation doesn't have a method commandsUsedInImplementation
                pass
        SystemRequirements.commandsRequired(commandsUsedInImplementations, verbose=verbose)

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations().
        
        This method in this very class is more of a demo, and usable for unit testing.
        An equivalent method in other classes could actually be useful."""
        return ["which"]

if __name__ == "__main__":
    print SystemRequirements.which("hostname")
    print SystemRequirements.commandsAvailable(["which", "hostname"])
    print SystemRequirements.commandsAvailable(["which", "hostname"], listWhich=True)
    print SystemRequirements.commandsRequired(["which", "hostname"])
    print SystemRequirements.commandsRequired(["which", "hostname"],
                                              verbose=True)
    SystemRequirements.commandsRequired(["which", "hostname", (["ifconfig"], ["ipconfig"])],
                                        verbose=True)
    SystemRequirements.commandsRequiredByImplementations([SystemRequirements],
                                                         verbose=True)
