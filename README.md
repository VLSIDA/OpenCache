# OpenCache
An open-source cache generator using [OpenRAM] SRAM arrays.

# What is OpenCache?
OpenCache is an open-source Python generator to create a cache design using OpenRAM's SRAM arrays.

# Documentation
[This](CACHE.md) serves as the documentation of OpenCache that explains how generated caches work.

# Dependencies
The OpenCache has the following dependencies:
+ Python 3.6 or higher
+ [nMigen] 0.2 or higher
+ [yosys] 0.9+4081 or higher

If want to verify the design via simulation and/or synthesis, you will need:
+ [OpenRAM]
+ [FuseSoC] 1.12 or higher
+ [Icarus] 10.3 or higher

For regression testing, you will need some Python packages, which can be installed with the following command:
```
pip3 install -r requirements.txt
```

# Usage
## Basic Usage
Clone the repository.
```
git clone https://github.com/VLSIDA/OpenCache.git
cd OpenCache/generator
```
Create a Python configuration file. All configuration parameters can be found in [here](CONFIG.md). A simple configuration file is:
```python
from policy import ReplacementPolicy, WritePolicy

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
replacement_policy = ReplacementPolicy.NONE

# write policy
write_policy = WritePolicy.WR_BACK

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

# Unit Tests
Regression testing performs a number of tests for OpenCache. From the generator directory, use the following command to run all regression tests:
```
python3 regress.py
```
To run a specific test:
```
python3 {unit test}.py
```

# License
OpenCache is licensed under the [BSD 3-clause License](LICENSE).

* * *

[OpenRAM]: https://github.com/VLSIDA/OpenRAM
[FuseSoC]: https://github.com/olofk/fusesoc
[Icarus]:  https://github.com/steveicarus/iverilog
[yosys]:   https://github.com/YosysHQ/yosys
[nMigen]:  https://github.com/nmigen/nmigen