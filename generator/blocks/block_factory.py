# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import os
import sys
import debug
from globals import OPTS


class block_factory:
    """
    This is a factory pattern to create block modules to be
    used in logic class.
    Logic blocks can be overridden for more specific Verilog
    design. This factory makes block instantiation easier.
    """

    def __init__(self):

        self.store_modules()


    def store_modules(self):
        """ Store modules in the blocks directory. """

        self.modules = []

        # FIXME: Assuming that OpenCache is run from the "generator" directory
        for module in os.listdir(format(sys.path[0] + "/blocks")):
            self.modules.append(os.path.basename(module).split(".")[0])


    def get_module_name(self, module_name):
        """ Return the real module name. """

        # If a module is extended, it should have the following name:
        #   {block name}_{policy name}
        overridden_name = "{0}_{1}".format(module_name, OPTS.replacement_policy)

        if overridden_name in self.modules:
            return overridden_name
        else:
            return module_name + "_base"


    def create(self, module_name, **kwargs):
        """ Create an instance of the given module. """

        real_module_name = self.get_module_name(module_name)

        import importlib
        c = importlib.reload(__import__(real_module_name))
        mod = getattr(c, real_module_name)

        debug.info(2, "Creating logic block: " + real_module_name)

        obj = mod(**kwargs)
        return obj


# Make a factory
factory = block_factory()