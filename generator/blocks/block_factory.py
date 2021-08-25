# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import sys
import os
import debug
from globals import OPTS


class block_factory:
    """
    This is a factory pattern to create block modules to be used in logic class.
    Logic blocks can be overridden for more specific Verilog design.
    This factory makes block instantiation easier.
    """

    def __init__(self):

        self.setup_paths()
        self.store_modules()


    def setup_paths(self):
        """ Include subdirectories for block modules. """
        debug.info(2, "Setting up block paths...")

        BLOCK_DIR = "{}/blocks".format(os.getenv("OPENCACHE_HOME"))

        # Add all of the subdirs to the Python path
        subdir_list = [item for item in os.listdir(BLOCK_DIR) if os.path.isdir(os.path.join(BLOCK_DIR, item))]
        for subdir in subdir_list:
            full_path = "{0}/{1}".format(BLOCK_DIR, subdir)
            # Use sys.path.insert instead of sys.path.append Python searches in
            # sequential order and common folders (such as verify) with OpenRAM
            # can result in importing wrong source codes.
            if "__pycache__" not in full_path:
                sys.path.insert(1, "{}".format(full_path))


    def store_modules(self):
        """ Store modules in the blocks directory. """

        BLOCK_DIR = "{}/blocks".format(os.getenv("OPENCACHE_HOME"))

        self.modules = []
        for _, _, modules in os.walk(BLOCK_DIR):
            for module in modules:
                if module.endswith(".py"):
                    self.modules.append(module.split(".")[0])


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