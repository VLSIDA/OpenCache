# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
"""
This is called globals.py, but it actually parses all the arguments
and performs the global OpenCache setup as well.
"""
import os
import debug
import shutil
import optparse
import options
import sys
import re
import copy
import importlib
import getpass

VERSION = "0.0.1"
NAME = "OpenCache v{}".format(VERSION)
USAGE = "opencache.py [options] <config file>\nUse -h for help.\n"

OPTS = options.options()
CHECKPOINT_OPTS = None


def parse_args():
    """ Parse the optional arguments for OpenCache. """

    global OPTS

    option_list = {
        optparse.make_option("-o",
                             "--output",
                             dest="output_name",
                             help="Base output file name(s) prefix",
                             metavar="FILE"),
        optparse.make_option("-p", "--outpath",
                             dest="output_path",
                             help="Output file(s) location"),
        optparse.make_option("-v", "--verbose",
                             action="count",
                             dest="verbose_level",
                             help="Increase the verbosity level"),
        optparse.make_option("-j", "--threads",
                             action="store",
                             type="int",
                             help="Specify the number of threads (default: 1)",
                             dest="num_threads"),
        optparse.make_option("-k", "--keeptemp",
                             action="store_true",
                             dest="keep_temp",
                             help="Keep the contents of the temp directory after a successful run"),
        optparse.make_option("--sim",
                             action="store_true",
                             dest="simulate",
                             help="Enable verification via simulation"),
        optparse.make_option("--syn",
                             action="store_true",
                             dest="synthesize",
                             help="Enable verification via synthesis")
        # -h --help is implicit.
    }

    parser = optparse.OptionParser(option_list=option_list,
                                   description=NAME,
                                   usage=USAGE,
                                   version=VERSION)

    (options, args) = parser.parse_args(values=OPTS)

    return (options, args)


def print_banner():
    """ Conditionally print the banner to stdout. """
    global OPTS

    if OPTS.is_unit_test or not OPTS.print_banner:
        return

    debug.print_raw("|==============================================================================|")
    debug.print_raw("|=========" + NAME.center(60) + "=========|")
    debug.print_raw("|=========" + " ".center(60) + "=========|")
    debug.print_raw("|=========" + "VLSI Design and Automation Lab".center(60) + "=========|")
    debug.print_raw("|=========" + "Computer Science and Engineering Department".center(60) + "=========|")
    debug.print_raw("|=========" + "University of California Santa Cruz".center(60) + "=========|")
    debug.print_raw("|=========" + " ".center(60) + "=========|")
    user_info = "Usage help: openram-user-group@ucsc.edu"
    debug.print_raw("|=========" + user_info.center(60) + "=========|")
    dev_info = "Development help: openram-dev-group@ucsc.edu"
    debug.print_raw("|=========" + dev_info.center(60) + "=========|")
    debug.print_raw("|=========" + "See LICENSE for license info".center(60) + "=========|")
    debug.print_raw("|==============================================================================|")


def check_versions():
    """ Run some checks of required software versions. """

    # FIXME: Which version is required?
    # NOTE: nMigen needs at least Python 3.6
    major_python_version = sys.version_info.major
    minor_python_version = sys.version_info.minor
    major_required = 3
    minor_required = 6
    if not (major_python_version == major_required and minor_python_version >= minor_required):
        debug.error("Python {0}.{1} or greater is required.".format(major_required, minor_required), -1)


def init_opencache(config_file, is_unit_test=True):
    """ Initialize the paths, variables, etc. """

    check_versions()

    debug.info(1, "Initializing OpenCache...")

    setup_paths()

    read_config(config_file, is_unit_test)

    fix_config()

    init_paths()

    global OPTS
    global CHECKPOINT_OPTS

    # This is a hack. If we are running a unit test and have checkpointed
    # the options, load them rather than reading the config file.
    # This way, the configuration is reloaded at the start of every unit test.
    # If a unit test fails,
    # we don't have to worry about restoring the old config values
    # that may have been tested.
    if is_unit_test and CHECKPOINT_OPTS:
        OPTS.__dict__ = CHECKPOINT_OPTS.__dict__.copy()
        return

    # Make a checkpoint of the options so we can restore
    # after each unit test
    if not CHECKPOINT_OPTS:
        CHECKPOINT_OPTS = copy.copy(OPTS)


def read_config(config_file, is_unit_test=True):
    """
    Read the configuration file that defines a few parameters. The
    config file is just a Python file that defines some config
    options. This will only actually get read the first time. Subsequent
    reads will just restore the previous copy (ask mrg)
    """
    global OPTS

    # it is already not an abs path, make it one
    if not os.path.isabs(config_file):
        config_file = os.getcwd() + "/" +  config_file

    # Make it a python file if the base name was only given
    config_file = re.sub(r'\.py$', "", config_file)

    # Expand the user if it is used
    config_file = os.path.expanduser(config_file)

    OPTS.config_file = config_file + ".py"
    # Add the path to the system path
    # so we can import things in the other directory
    dir_name = os.path.dirname(config_file)
    module_name = os.path.basename(config_file)

    # Check that the module name adheres to Python's module naming conventions.
    # This will assist the user in interpreting subsequent errors in loading
    # the module. Valid Python module naming is described here:
    #   https://docs.python.org/3/reference/simple_stmts.html#the-import-statement
    if not module_name.isidentifier():
        debug.error("Configuration file name is not a valid Python module name: "
                    "{0}. It should be a valid identifier.".format(module_name))

    # Prepend the path to avoid if we are using the example config
    sys.path.insert(0, dir_name)
    # Import the configuration file of which modules to use
    debug.info(1, "Configuration file is " + config_file + ".py")
    try:
        config = importlib.import_module(module_name)
    except:
        debug.error("Unable to read configuration file: {0}".format(config_file), 2)

    OPTS.overridden = {}
    for k, v in config.__dict__.items():
        # The command line will over-ride the config file
        # Note that if we re-read a config file, nothing will get read again!
        if k not in OPTS.__dict__:
            OPTS.__dict__[k] = v
            OPTS.overridden[k] = True

    OPTS.is_unit_test = is_unit_test


def fix_config():
    """ Fix and update options from the config file. """

    # Convert policy strings to enum values
    from policy import replacement_policy as RP
    OPTS.replacement_policy = RP.get_value(OPTS.replacement_policy)
    from policy import write_policy as WP
    OPTS.write_policy = WP.get_value(OPTS.write_policy)

    # If config didn't set output name, make a reasonable default
    if OPTS.output_name == "":
        OPTS.output_name = "cache_{0}b_{1}b_{2}_{3!s}".format(OPTS.total_size,
                                                              OPTS.word_size,
                                                              OPTS.num_ways,
                                                              OPTS.replacement_policy)
        if OPTS.is_unit_test:
            OPTS.output_name = "uut"

    # If config didn't set SRAM array names, make reasonable defaults
    if OPTS.tag_array_name == "":
        OPTS.tag_array_name = "{}_tag_array".format(OPTS.output_name)
    if OPTS.data_array_name == "":
        OPTS.data_array_name = "{}_data_array".format(OPTS.output_name)
    if OPTS.use_array_name == "":
        OPTS.use_array_name = "{}_use_array".format(OPTS.output_name)

    # Massage the output path to be an absolute one
    if not OPTS.output_path.endswith('/'):
        OPTS.output_path += "/"
    if not OPTS.output_path.startswith('/'):
        OPTS.output_path = os.getcwd() + "/" + OPTS.output_path

    # Create a new folder for each process of unit tests
    if OPTS.is_unit_test:
        OPTS.output_path += "opencache_{0}_{1}/".format(getpass.getuser(),
                                                        os.getpid())
    # Create a new folder for this run if not unit test
    else:
        OPTS.output_path += OPTS.output_name + "/"

    debug.info(1, "Output saved in " + OPTS.output_path)

    # Make a temp folder if not given
    # This folder is used for verification files
    if OPTS.temp_path == "":
        OPTS.temp_path = OPTS.output_path + "tmp/"


def end_opencache():
    """ Clean up OpenCache for a proper exit. """

    cleanup_paths()


def cleanup_paths():
    """ We should clean up the temp directory after execution. """
    global OPTS

    if OPTS.keep_temp:
        debug.info(1, "Preserving temp directory: {}".format(OPTS.temp_path))
        return
    elif os.path.exists(OPTS.temp_path):
        purge_temp()


def purge_temp():
    """ Remove the temp folder. """

    debug.info(1, "Purging temp directory: {}".format(OPTS.temp_path))

    # Remove all files and subdirectories under the temp directory
    shutil.rmtree(OPTS.temp_path, ignore_errors=True)


def setup_paths():
    """ Include script directories to the sys path. """
    debug.info(2, "Setting up paths...")

    try:
        OPENCACHE_HOME = os.getenv("OPENCACHE_HOME")
    except:
        debug.error("$OPENCACHE_HOME is not properly defined.", 1)
    debug.check(os.path.isdir(OPENCACHE_HOME),
                "$OPENCACHE_HOME does not exist: {0}".format(OPENCACHE_HOME))

    # If OPENRAM_HOME is added to PYTHONPATH, remove it for this program since
    # it can cause OpenCache to import wrong source codes.
    try:
        OPENRAM_HOME = os.getenv("OPENRAM_HOME")
        if OPENRAM_HOME in sys.path:
            sys.path.remove(OPENRAM_HOME)
    except:
        debug.warning("$OPENRAM_HOME is not properly defined.")

    # Add all of the subdirs to the Python path
    subdir_list = [item for item in os.listdir(OPENCACHE_HOME) if os.path.isdir(os.path.join(OPENCACHE_HOME, item))]
    for subdir in subdir_list:
        full_path = "{0}/{1}".format(OPENCACHE_HOME, subdir)
        if "__pycache__" not in full_path:
            sys.path.append(full_path)


def init_paths():
    """ Create the output directory if it doesn't exist. """

    # Make the output directory
    make_dir(OPTS.output_path, "output")

    # Make the temp directory if only needed
    if OPTS.simulate or OPTS.synthesize or OPTS.is_unit_test:
        make_dir(OPTS.temp_path, "temp")


def make_dir(path, name="a"):
    """ Make a directory. """

    # Don't delete the dir, it may have other files!
    # Make the directory if it doesn't exist
    try:
        debug.info(1, "Creating {0} directory: {1}".format(name, path))
        os.makedirs(path, 0o750)
    except OSError as e:
        if e.errno == 17: # errno.EEXIST
            os.chmod(path, 0o750)
    except:
        debug.error("Unable to make {} directory.".format(name), -1)


def is_exe(fpath):
    """ Return true if the given is an executable file that exists. """

    return os.path.exists(fpath) and os.access(fpath, os.X_OK)


def find_exe(check_exe):
    """ Check if the binary exists in any path dir and return the full path. """

    # Check if the executable exists in the path
    for path in os.environ["PATH"].split(os.pathsep):
        exe = os.path.join(path, check_exe)
        if is_exe(exe):
            return exe
    return None


def print_time(name, now_time, last_time=None, indentation=2):
    """ Print a statement about the time delta. """
    global OPTS

    # Don't print during testing
    if not OPTS.is_unit_test or OPTS.verbose_level > 0:
        if last_time:
            time = str(round((now_time - last_time).total_seconds(), 1)) + " seconds"
        else:
            time = now_time.strftime('%m/%d/%Y %H:%M:%S')
        debug.print_raw("{0} {1}: {2}".format("*" * indentation, name, time))


def report_status():
    """
    Check for valid arguments and report the info about the cache being
    generated.
    """
    global OPTS

    # Check if argument types are correct
    if type(OPTS.total_size) is not int:
        debug.error("{} is not an integer in config file.".format(OPTS.total_size))
    if type(OPTS.word_size) is not int:
        debug.error("{} is not an integer in config file.".format(OPTS.word_size))
    if type(OPTS.words_per_line) is not int:
        debug.error("{} is not an integer in config file.".format(OPTS.words_per_line))
    if type(OPTS.address_size) is not int:
        debug.error("{} is not an integer in config file.".format(OPTS.address_size))
    if type(OPTS.num_ways) is not int:
        debug.error("{} is not an integer in config file.".format(OPTS.num_ways))
    if type(OPTS.openram_options) is not dict:
        debug.error("{} is not a dictionary in config file.".format(OPTS.openram_options))

    # Data array's total size should match the word size
    if OPTS.total_size % OPTS.word_size:
        debug.error("Total size is not divisible by word size.", -1)

    # If write size is specified, word size should be divisible by it
    if OPTS.write_size is not None and OPTS.word_size % OPTS.write_size:
        debug.error("Word size is not divisible by write size.", -1)

    from policy import replacement_policy as RP
    # Direct-mapped cache doesn't have a replacement policy
    if OPTS.num_ways == 1 and OPTS.replacement_policy != RP.NONE:
        debug.error("Direct-mapped cache cannot have a replacement policy.", -1)
    # N-way or Fully Associative caches should have a replacement policy
    if OPTS.num_ways > 1 and OPTS.replacement_policy == RP.NONE:
        debug.error("N-way Set Associative and Fully Associative caches need replacement policy.", -1)

    # Options below are not implemented yet
    if not OPTS.is_data_cache:
        debug.error("Instruction cache is not yet supported.", -1)
    from policy import write_policy as WP
    if OPTS.write_policy != WP.WRITE_BACK:
        debug.error("Only write-back policy is supported at the moment.", -1)
    if OPTS.return_type != "word":
        debug.error("Only returning word is supported at the moment.", -1)

    # Print cache info
    debug.print_raw("\nCache type: {}".format("Data" if OPTS.is_data_cache else "Instruction"))
    debug.print_raw("Word size: {}".format(OPTS.word_size))
    debug.print_raw("Words per line: {}".format(OPTS.words_per_line))
    debug.print_raw("Number of ways: {}".format(OPTS.num_ways))
    debug.print_raw("Replacement policy: {}".format(OPTS.replacement_policy.long_name()))
    debug.print_raw("Write policy: {}".format(OPTS.write_policy.long_name()))
    debug.print_raw("Return type: {}".format(OPTS.return_type.capitalize()))
    debug.print_raw("Data hazard: {}\n".format(OPTS.data_hazard))