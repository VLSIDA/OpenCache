# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from amaranth import C
from policy import replacement_policy as rp
from globals import OPTS


class hit_detector:
    """
    This is the module that implements hit/miss detection logic.
    """

    def __init__(self, c, m):

        self.c = c
        self.m = m


    def check_hit(self, way=0):
        """ Return Amaranth context manager instance to check hit. """

        # Request is hit if valid bit is set and address' tag matches the way's tag
        return self.m.If(self.c.tag_array.output().valid(way) & (self.c.tag_array.output().tag(way) == self.c.tag))


    def check_clean_miss(self):
        """ Return Amaranth context manager instance to check clean miss. """

        if self.c.has_dirty:
            # Assume clean miss if not dirty miss
            return self.m.Else()
        else:
            # Assume clean miss
            return self.m.If(1)


    def check_dirty_miss(self, way=0):
        """ Return Amaranth context manager instance to check dirty miss. """

        # Assume dirty miss if valid and dirty bits of the way are set
        return self.m.If(self.c.tag_array.output().valid(way) & self.c.tag_array.output().dirty(way))


    def find_hit(self):
        """ Return the way hit and wrap the statements accordingly. """

        if OPTS.replacement_policy == rp.NONE:
            return self.find_hit_direct()
        else:
            return self.find_hit_n_way()


    def find_miss(self):
        """
        Return whether miss is dirty, the way missed, and wrap the statements
        accordingly.
        """

        if OPTS.replacement_policy == rp.NONE:
            return self.find_miss_none()
        elif OPTS.replacement_policy == rp.FIFO:
            return self.find_miss_fifo()
        elif OPTS.replacement_policy == rp.LRU:
            return self.find_miss_lru()
        elif OPTS.replacement_policy == rp.RANDOM:
            return self.find_miss_random()


    def find_empty(self):
        """ Return the empty way and wrap the statements accordingly. """

        if OPTS.replacement_policy == rp.RANDOM:
            for i in range(self.c.num_ways):
                with self.m.If(~self.c.tag_array.output().valid(i)):
                    yield i


    def find_hit_direct(self):
        """ Return the way hit for direct-mapped caches. """

        with self.check_hit():
            yield 0


    def find_hit_n_way(self):
        """ Return the way hit for N-way set associative caches. """

        for i in range(self.c.num_ways):
            with self.check_hit(i):
                yield i


    def find_miss_none(self):
        """ Return the way missed for direct-mapped caches. """

        # Instruction caches don't have dirty bit
        if self.c.has_dirty:
            with self.check_dirty_miss():
                yield True, 0
        with self.check_clean_miss():
            yield False, 0


    def find_miss_fifo(self):
        """ Return the way missed for FIFO caches. """

        # Instruction caches don't have dirty bit
        if self.c.has_dirty:
            with self.check_dirty_miss(self.c.use_array.output()):
                with self.m.Switch(self.c.use_array.output()):
                    for i in range(self.c.num_ways):
                        with self.m.Case(i):
                            yield True, i
        with self.check_clean_miss():
            yield False, 0


    def find_miss_lru(self):
        """ Return the way missed for LRU caches. """

        for i in range(self.c.num_ways):
            with self.m.If(self.c.use_array.output().use(i) == C(0, self.c.way_size)):
                # Instruction caches don't have dirty bit
                if self.c.has_dirty:
                    with self.check_dirty_miss(i):
                        yield True, i
                with self.check_clean_miss():
                    yield False, i


    def find_miss_random(self):
        """ Return the way missed for random caches. """

        # Instruction caches don't have dirty bit
        if self.c.has_dirty:
            with self.check_dirty_miss(self.c.random):
                with self.m.Switch(self.c.random):
                    for i in range(self.c.num_ways):
                        with self.m.Case(i):
                            yield True, i
        with self.check_clean_miss():
            yield False, 0