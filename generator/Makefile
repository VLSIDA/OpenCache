CUR_DIR = $(shell pwd)
TEST_DIR = ${CUR_DIR}/tests

# MAKEFLAGS += -j 1

# Code format tests
FORMAT_TESTS = $(shell find ${TEST_DIR} -name 00*_test.py)

# Simulator tests (sim_cache)
SIM_TESTS = $(shell find ${TEST_DIR} -name 01*_test.py)

# Verification tests (simulation and synthesis)
VERIFY_TESTS = $(shell find ${TEST_DIR} -name 0[2-4]*_test.py)

ALL_TESTS = \
${FORMAT_TESTS} \
${SIM_TESTS} \
${VERIFY_TESTS}

.PHONY: ${ALL_TESTS}

all: ${ALL_TESTS}

# Code format tests
format: ${FORMAT_TESTS}

# Simulator tests
sim: ${SIM_TESTS}

# Verification tests
verify: ${VERIFY_TESTS}

$(ALL_TESTS):
	python3 $@
