# Benchmark commands
BASE_URL ?= https://benchmark-dr-s-2799835ad04b501a95044223ae72ced7.staging.langgraph.app
SLOWEST_N ?= 2
RAMP_START ?= 40
RAMP_END ?= 1000
RAMP_MULTIPLIER ?= 2
WAIT_SECONDS ?= 60
CLEAR_BETWEEN_STEPS ?= true
CLEAR_DELAY_SECONDS ?= 5
DATA_SIZE ?= 1000
DELAY ?= 0
EXPAND ?= 1
STEPS ?= 100

benchmark-burst:
	make benchmark-reset
	k6 run burst.js

benchmark-ramp:
	make benchmark-reset
	k6 run --out json=raw_data_$(shell date +%Y-%m-%dT%H-%M-%S).json --system-tags=[] ramp.js

benchmark-capacity:
	rm -f capacity_summary_t*.json capacity_raw_t*.json capacity_histogram_*.json
	npm install
	BASE_URL=$(BASE_URL) \
	SLOWEST_N=$(SLOWEST_N) \
	RAMP_START=$(RAMP_START) \
	RAMP_END=$(RAMP_END) \
	RAMP_MULTIPLIER=$(RAMP_MULTIPLIER) \
	WAIT_SECONDS=$(WAIT_SECONDS) \
	CLEAR_BETWEEN_STEPS=$(CLEAR_BETWEEN_STEPS) \
	CLEAR_DELAY_SECONDS=$(CLEAR_DELAY_SECONDS) \
	DATA_SIZE=$(DATA_SIZE) \
	DELAY=$(DELAY) \
	EXPAND=$(EXPAND) \
	STEPS=$(STEPS) \
	node capacity_runner.mjs

benchmark-charts:
	npm install
	node graphs.js $(shell ls -t raw_data_*.json | head -1) true

benchmark-reset:
	node clean.js

benchmark-new-revision:
	node update-revision.js

benchmark-clean:
	rm -f results_*.json summary_*.json raw_data_*.json *_chart_*.png

benchmark-clean-charts:
	rm -f *_chart_*.png

# Mixed workload benchmark - tests quick runs competing with long runs
QUICK_VUS ?= 250
QUICK_ITERATIONS ?= 1000
QUICK_STEPS ?= 5
QUICK_DATA_SIZE ?= 100
QUICK_MAX_WAIT_SECONDS ?= 120
QUICK_POLL_INTERVAL ?= 2
LONG_VUS ?= 5
LONG_ITERATIONS ?= 10
LONG_STEPS ?= 50
LONG_DELAY ?= 1
LONG_DATA_SIZE ?= 10000
LONG_MAX_WAIT_SECONDS ?= 200
LONG_POLL_INTERVAL ?= 5

benchmark-mixed:
	rm -f mixed_workload_*.json
	npm install
	BASE_URL=$(BASE_URL) \
	SLOWEST_N=$(SLOWEST_N) \
	QUICK_VUS=$(QUICK_VUS) \
	QUICK_ITERATIONS=$(QUICK_ITERATIONS) \
	QUICK_STEPS=$(QUICK_STEPS) \
	QUICK_DATA_SIZE=$(QUICK_DATA_SIZE) \
	QUICK_MAX_WAIT_SECONDS=$(QUICK_MAX_WAIT_SECONDS) \
	QUICK_POLL_INTERVAL=$(QUICK_POLL_INTERVAL) \
	LONG_VUS=$(LONG_VUS) \
	LONG_ITERATIONS=$(LONG_ITERATIONS) \
	LONG_STEPS=$(LONG_STEPS) \
	LONG_DELAY=$(LONG_DELAY) \
	LONG_DATA_SIZE=$(LONG_DATA_SIZE) \
	LONG_MAX_WAIT_SECONDS=$(LONG_MAX_WAIT_SECONDS) \
	LONG_POLL_INTERVAL=$(LONG_POLL_INTERVAL) \
	node mixed_workload_runner.mjs
