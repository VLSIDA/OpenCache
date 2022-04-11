=====================
Configuration Options
=====================
This is the list of all configuration options of OpenCache.

--------------------
Necessary Parameters
--------------------
**********
total_size
**********
This is the total size of the data array of the cache. It must be divisible by
the **word_size** parameter.

*********
word_size
*********
This is the bit size of a word.

**************
words_per_line
**************
This is the number of words per line.

************
address_size
************
This is the bit size of the address port of the cache.

-------------------
Optional Parameters
-------------------
**********
write_size
**********
This is the bit size that corresponds to a write mask bit. Write masks are not
used by default. If **write_size** is valid (**word_size** is divisible by it),
write mask will be added to the CPU interface.

********
num_ways
********
This is the number of ways in the cache.

******************
replacement_policy
******************
This is the replacement (eviction) policy of the cache. Note that direct-mapped
caches (1-way) do not have a replacement policy. Currently supported
replacement policies are:

+ First In First Out (FIFO)
+ Least Recently Used (LRU)
+ Random

************
write_policy
************
This is the write policy of the cache. Currently supported write policies are:

+ Write-back
+ Write-through

*************
read_only
*************
This is whether the cache is a *"data cache"* or an *"instruction cache"*.

***********
return_type
***********
This is which data the cache returns. Currently supported return types are:

+ Word
+ Line

***********
has_flush
***********
This is whether the cache has flush signal.

***********
data_hazard
***********
This is whether data hazard may occur in the internal SRAM arrays. Some
technologies do not have read-after-write bitcells which might cause data
hazard in the cache. If **data_hazard** is True, generated caches will avoid
causing this kind of data hazard. However, this parameter can be set to False
if the user can guarantee that SRAM arrays are going to be *"data hazard
proof"*.

***********
output_path
***********
This is where output files are going to be saved to.

***********
output_name
***********
This is what the names of output files are going to be.

**************
tag_array_name
**************
This is the name of the tag array module.

***************
data_array_name
***************
This is the name of the data array module.

**************
use_array_name
**************
This is the name of the use array module.

***************
openram_options
***************
OpenRAM has many options for configuration which are not specified by OpenCache
generated configuration files. If you want to generate configuration files with
specific options, you can use ``openram_options`` like the following:

.. code-block:: python

    openram_options = {
        "tech_name": "scn4m_subm",
        "nominal_corner_only": True,
        "analytical_delay": False,
    }

************
trim_verilog
************
This is whether the Verilog output has various signals and comments generated
by Yosys.

-----------------------
Verification Parameters
-----------------------
********
simulate
********
This is whether to simulate the design after saving files.

**********
synthesize
**********
This is whether to synthesize the design after saving files.

*********
temp_path
*********
This is where temporary verification files are going to be saved to.

*********
keep_temp
*********
This is whether to keep temporary verification files after verification.

***********
run_openram
***********
This is whether to run OpenRAM for verification. If the output of it has
already been generated, this can be set to False for faster verification.

******************
keep_openram_files
******************
This is whether to keep OpenRAM files after running OpenRAM for verification.
OpenRAM may generate large files; therefore, set this to False to delete
unnecessary files.

********
sim_size
********
This is the number of read/write operations performed during the simulation of
the design.

***********
num_threads
***********
This is the number of threads for regression testing.

*************
verbose_level
*************
This is the verbosity level of OpenCache.