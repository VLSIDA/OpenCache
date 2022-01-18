# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from globals import OPTS


class logic_base:
    """
    This is the base class of logic modules.
    Methods of this class can be overridden for specific implementation of each logic.
    """

    def __init__(self):
        pass


    def add(self, c, m):
        """ Add all sections of the always block code. """

        self.add_states(c, m)
        self.add_flush_sig(c, m)
        self.add_reset_sig(c, m)


    def add_states(self, c, m):
        """ Add statements for each cache state. """

        with m.Switch(c.state):
            self.add_reset(c, m)
            self.add_flush(c, m)
            self.add_idle(c, m)
            self.add_compare(c, m)
            self.add_write(c, m)
            self.add_wait_write(c, m)
            self.add_read(c, m)
            self.add_wait_read(c, m)
            if OPTS.data_hazard:
                self.add_flush_hazard(c, m)
                self.add_wait_hazard(c, m)


    def add_reset(self, c, m):
        """ Add statements for the RESET state. """
        pass


    def add_flush(self, c, m):
        """ Add statements for the FLUSH state. """
        pass


    def add_idle(self, c, m):
        """ Add statements for the IDLE state. """
        pass


    def add_compare(self, c, m):
        """ Add statements for the COMPARE state. """
        pass


    def add_write(self, c, m):
        """ Add statements for the WRITE state. """
        pass


    def add_wait_write(self, c, m):
        """ Add statements for the WAIT_WRITE state. """
        pass


    def add_read(self, c, m):
        """ Add statements for the READ state. """
        pass


    def add_wait_read(self, c, m):
        """ Add statements for the WAIT_READ state. """
        pass


    def add_flush_hazard(self, c, m):
        """ Add statements for the FLUSH_HAZARD state. """
        pass


    def add_wait_hazard(self, c, m):
        """ Add statements for the WAIT_HAZARD state. """
        pass


    def add_flush_sig(self, c, m):
        """ Add flush signal control. """
        pass


    def add_reset_sig(self, c, m):
        """ Add reset signal control. """
        pass