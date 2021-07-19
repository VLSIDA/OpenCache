# OpenCache
An open-source cache generator using [OpenRAM] SRAM arrays.

# What is OpenCache?
OpenCache is an open-source Python generator to create a cache design using OpenRAM's SRAM arrays.

# Documentation
[This](CACHE.md) serves as the documentation of OpenCache that explains how generated caches work.

# Dependencies
The OpenCache has only one dependency:
+ Python 3.5 or higher

If you are going to verify the design via simulation and/or synthesis, you will need:
+ [OpenRAM] and all of its dependencies
+ [FuseSoC]
+ [Icarus] (for simulation)
+ [yosys] (for synthesis)

# Usage
## Basic Usage
Clone the repository.
```
git clone git@github.com:biarmic/OpenCache.git
cd OpenCache/generator
```
Create a Python configuration file. All configuration parameters can be found in [here](CONFIG.md). A simple configuration file is:
```python
# data array size
total_size = 1024

# data word bit size
word_size = 8

# number of words per line
words_per_line = 4

# address port size
address_size = 11

# number of ways
num_ways = 1

# replacement policy
replacement_policy = None

# output file name
output_name = "cache"
```
Run the generator.
```
python3 opencache.py config_file
```

## Verification
In order to run the verification, you need to add the following lines to your configurtion file.
```python
# for simulation
simulate = True

# for synthesis
synthesize = True

# to keep the results
keep_temp = True
```

# License
OpenCache is licensed under the [BSD 3-clause License](LICENSE).

* * *

[OpenRAM]: https://github.com/VLSIDA/OpenRAM
[FuseSoC]: https://github.com/olofk/fusesoc
[Icarus]:  https://github.com/steveicarus/iverilog
[yosys]:   https://github.com/YosysHQ/yosys