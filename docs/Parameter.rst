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
This is the total size of the data array of the cache. It must match `word_size` parameter.

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
This is the bit size of address port of the cache.

-------------------
Optional Parameters
-------------------
********
num_ways
********
This is the number of the ways in the cache.

******************
replacement_policy
******************
This is the replacement (eviction) policy of the cache. Note that direct-mapped caches
(1-way) do not have a replacement policy. Currently supported replacement policies are:
* First In First Out (FIFO)
* Least Recently Used (LRU)
* Random

************
write_policy
************
This is the write policy of the cache. Currently supported write policies are:
* Write-back

*************
is_data_cache
*************
This is whether the cache is a *"data cache"* or an *"instruction cache"*. INSTRUCTION
CACHE IS NOT YET SUPPORTED!

***********
return_type
***********
This is which data the cache returns. Currently supported return types are:
* Word

***********
data_hazard
***********
This is whether data hazard may occur in the internal SRAM arrays. Currently OpenRAM SRAM
arrays are not read-after-write. However, this parameter can be set `False` if the user
can guarantee that SRAM arrays are going to be *"data hazard proof"* or OpenRAM SRAM arrays
are read-after-write in the future.

***********
output_path
***********
This is where output files are going to be saved to.

***********
output_name
***********
This is what the names of output files are going to be.

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
This is whether to run OpenRAM for verification. If the output of it has already been
generated, this can be set False for faster verification.

********
sim_size
********
This is the number of read/write operations performed during the simulation of the design.

***********
num_threads
***********
This is the number of threads for regression testing.