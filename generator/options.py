import optparse
import getpass
import os

class options(optparse.Values):
    """
    Class for holding all of the OpenCache options. All
    of these options can be over-riden in a configuration file
    that is the sole required command-line positional argument for opencache.py.
    """

    #########################
    # Configuration options #
    #########################

    # These parameters must be specified by user in config file.
    # total_size = 0
    # word_size = 0
    # words_per_line = 0
    # address_size = 0

    # Currently supports direct and n-way caches
    num_ways = 1
    # Replacement policy of the cache
    replacement_policy = None

    # Cache can be write-back or write-through !! write-through not yet supported !!
    write_policy = "write-back"
    # Cache can be a data cache or an instruction cache !! instruction cache not yet supported !!
    is_data_cache = True
    # Cache can return a word or a line of words !! returning line not yet supported !!
    return_type = "word"

    # Data hazard might occur when the same location is read and
    # written at the same cycle. If SRAM arrays are guaranteed to
    # be data hazard proof, this can be False.
    data_hazard = True

    # Define the output file paths
    output_path = "."
    # Define the output file base name
    output_name = ""

    verbose_level = 0

    debug = False