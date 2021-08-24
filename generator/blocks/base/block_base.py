# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from globals import OPTS


class block_base:
    """
    This is the base class of always block modules.
    Methods of this class can be overridden for specific implementation of each
    always block.
    """

    def __init__(self):
        pass


    def add(self, dsgn, m):
        """ Add all sections of the always block code. """

        self.add_states(dsgn, m)
        self.add_flush_sig(dsgn, m)
        self.add_reset_sig(dsgn, m)


    def add_states(self, dsgn, m):
        """ Add statements for each cache state. """

        with m.Switch(dsgn.state):
            self.add_reset(dsgn, m)
            self.add_flush(dsgn, m)
            self.add_idle(dsgn, m)
            if OPTS.data_hazard:
                self.add_wait_hazard(dsgn, m)
            self.add_compare(dsgn, m)
            self.add_write(dsgn, m)
            self.add_wait_write(dsgn, m)
            self.add_read(dsgn, m)
            self.add_wait_read(dsgn, m)


    def add_reset(self, dsgn, m):
        """ Add statements for the RESET state. """
        pass


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """
        pass


    def add_idle(self, dsgn, m):
        """ Add statements for the IDLE state. """
        pass


    def add_wait_hazard(self, dsgn, m):
        """ Add statements for the WAIT_HAZARD state. """
        pass


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """
        pass


    def add_write(self, dsgn, m):
        """ Add statements for the WRITE state. """
        pass


    def add_wait_write(self, dsgn, m):
        """ Add statements for the WAIT_WRITE state. """
        pass


    def add_read(self, dsgn, m):
        """ Add statements for the READ state. """
        pass


    def add_wait_read(self, dsgn, m):
        """ Add statements for the WAIT_READ state. """
        pass


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """
        pass


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """
        pass