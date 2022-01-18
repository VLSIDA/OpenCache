# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import os
import sys
from globals import OPTS


class replacer:
    """
    This class is used to import and add the replacement policy logic from the
    ./replacers directory.
    """

    def __init__(self):
        pass


    def add(self, c, m):
        """ Add the replacer logic corresponding to the replacement policy. """

        logic = self.get_replacer()
        if logic:
            logic.add(c, m)


    def get_replacer(self, **kwargs):
        """ Get the replacer logic of the replacement policy. """

        name = "{0}_replacer".format(OPTS.replacement_policy)
        path = "{0}/logic/replacers/".format(os.getenv("OPENCACHE_HOME"))

        # Check if file exists
        if os.path.isfile("{0}{1}.py".format(path, name)):
            # Append the file to sys.path
            sys.path.append(path)

            # Import the module
            import importlib
            c = importlib.reload(__import__(name))
            mod = getattr(c, name)

            # Create instance and return
            obj = mod(**kwargs)
            return obj