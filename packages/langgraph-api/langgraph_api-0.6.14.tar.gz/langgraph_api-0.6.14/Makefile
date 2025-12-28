.PHONY: build release lint format test test_watch start start-inmem start-inmem-license-oss start start-js-server build-go-server start-go-server stop-go-server check-version check-base-imports

# Environment variables
FF_USE_CORE_API ?= false
LANGSERVE_GRAPHS_ALL = '{"agent": {"path": "./tests/graphs/agent.py:graph", "description": "agent"}, "custom_lifespan": "./tests/graphs/my_router.py:graph", "single_node": "./tests/graphs/single_node.py:graph", "benchmark": "./tests/graphs/benchmark.py:graph", "config_graph": "./tests/graphs/config_graph.py:graph", "other": "./tests/graphs/other.py:make_graph", "weather": "./tests/graphs/weather.py:mk_weather_graph", "searchy": "./tests/graphs/searchy.py:graph", "agent_simple": "./tests/graphs/agent_simple.py:graph", "simple_runtime": "./tests/graphs/simple_runtime.py:graph", "agent_interrupt": "./tests/graphs/agent_interrupt.py:graph", "message_type_test": "./tests/graphs/message_type_test.py:graph", "remote_subgraph_parent": "./tests/graphs/remote_subgraph_parent.py:graph", "simple_remote": "./tests/graphs/simple_remote.py:graph", "nested_subgraphs": "./tests/graphs/nested_subgraphs.py:graph", "functional_fibonacci": "./tests/graphs/functional_fibonacci.py:fibonacci", "state_graph_fibonacci": "./tests/graphs/state_graph_fibonacci.py:fibonacci"}'
LANGSERVE_GRAPHS_AUTH = '{"agent": {"path": "./tests/graphs/agent.py:graph", "description": "agent"}, "config_graph": "./tests/graphs/config_graph.py:graph", "other": "./tests/graphs/other.py:make_graph", "weather": "./tests/graphs/weather.py:mk_weather_graph", "searchy": "./tests/graphs/searchy.py:graph", "agent_simple": "./tests/graphs/agent_simple.py:graph", "simple_runtime": "./tests/graphs/simple_runtime.py:graph", "functional_fibonacci": "./tests/graphs/functional_fibonacci.py:fibonacci", "state_graph_fibonacci": "./tests/graphs/state_graph_fibonacci.py:fibonacci"}'

# Go server management
build-go-server:
	@echo "Building core-server..."
	$(MAKE) -C ../core build-core-server

start-go-server: # NOTE: core server will start with sqlite if no DATABASE_URI is provided
	@echo "Starting Core API (SQLite) gRPC server on port 50051..."
	cd ../core && \
	FF_USE_CORE_API=true \
	LANGSERVE_GRAPHS=$(LANGSERVE_GRAPHS_ALL) \
	DATABASE_URI= \
	REDIS_URI= \
	./bin/core-server \
		-service core-api \
		-apply-db-schema &
	@sleep 2

stop-go-server:
	@echo "Stopping Core API gRPC server on port 50051..."
	@lsof -ti:50051 | xargs -r kill -9 || echo "No process found on port 50051"

# lint commands

lint:
	uv run ruff check . --exclude "**/generated/**"
	uv run ruff format . --diff --exclude "**/generated/**"
	uv run ty check --exclude "**/pb/**" --exclude "**/*_test.py" --exclude "**/test_*.py" --exclude "**/tests/**" --exclude "venv/**" --exclude ".venv/**" --exclude "build/**" --exclude "dist/**" --exclude "**/generated/**" .

format:
	uv run ruff check --fix . --exclude "**/generated/**"
	uv run ruff format . --exclude "**/generated/**"

check-base-imports:
	LANGGRAPH_RUNTIME_EDITION=inmem DATABASE_URI=:memory: REDIS_URI=_FAKE uv run python -c "from langgraph_api.config import *; from langgraph_runtime import *"

# test commands

TEST ?= tests/ ../runtime_inmem/tests/
AUTH_TEST ?= "tests/integration_tests/test_custom_auth.py"
LANGGRAPH_HTTP ?= {"disable_mcp": false, "disable_a2a": false}
LANGGRAPH_AES_KEY ?= '1234567890123456'
BG_JOB_TIMEOUT_SECS ?= 3600

ifeq ($(LANGGRAPH_HTTP),fastapi)
	HTTP_CONFIG := {"app": "./tests/graphs/my_router.py:app", "disable_mcp": false, "disable_a2a": false, "mount_prefix": "/my-cool/api"}
else
	HTTP_CONFIG := $(LANGGRAPH_HTTP)
endif

LANGGRAPH_STORE ?= ""
ifeq ($(LANGGRAPH_STORE),custom)
	STORE_CONFIG := {"path": "./tests/graphs/custom_store.py:generate_store"}
else
	STORE_CONFIG := {"index": {"dims": 500, "embed": "./tests/graphs/test_utils/embeddings.py:embeddings"}}
endif

REVISION ?= $(shell git rev-parse --short HEAD)
LANGGRAPH_ENCRYPTION ?=

test-license-oss:
	@if [ "$(FF_USE_CORE_API)" = "true" ]; then \
		LANGGRAPH_RUNTIME_EDITION=inmem LANGGRAPH_HTTP='$(HTTP_CONFIG)' LANGGRAPH_STORE='$(STORE_CONFIG)' LANGGRAPH_ENCRYPTION='$(LANGGRAPH_ENCRYPTION)' REDIS_URI=_FAKE DATABASE_URI=:memory: MIGRATIONS_PATH=__inmem__ FF_USE_CORE_API=true uv run pytest -m sqlite_grpc -v $(TEST); \
	else \
		LANGGRAPH_RUNTIME_EDITION=inmem LANGGRAPH_HTTP='$(HTTP_CONFIG)' LANGGRAPH_STORE='$(STORE_CONFIG)' LANGGRAPH_ENCRYPTION='$(LANGGRAPH_ENCRYPTION)' REDIS_URI=_FAKE DATABASE_URI=:memory: MIGRATIONS_PATH=__inmem__ uv run pytest -v $(TEST); \
	fi

test-watch-oss:
	LANGGRAPH_RUNTIME_EDITION=inmem LANGGRAPH_HTTP='$(HTTP_CONFIG)' LANGGRAPH_ENCRYPTION='$(LANGGRAPH_ENCRYPTION)' REDIS_URI=_FAKE DATABASE_URI=:memory: MIGRATIONS_PATH=__inmem__ uv run --no-sync ptw . -- -x -vv --ff --capture=no $(TEST)

test: test-license-oss
test-watch: test-watch-oss
unit-test:
	DATABASE_URI="test" REDIS_URI="test" uv run pytest tests/unit_tests

test-auth:
	LANGGRAPH_RUNTIME_EDITION=inmem LANGGRAPH_AUTH='{"path": "./tests/graphs/fastapi_jwt_auth.py:get_current_active_user"}' REDIS_URI=_FAKE DATABASE_URI=:memory: MIGRATIONS_PATH=__inmem__ uv run pytest -v $(AUTH_TEST)


define FASTAPI_JWT_AUTH_TEST
	LANGGRAPH_RUNTIME_EDITION=inmem \
	LANGGRAPH_AUTH='{"path": "./tests/graphs/fastapi_jwt_middleware_ordering.py:auth"}' \
	REDIS_URI=_FAKE \
	DATABASE_URI=:memory: \
	MIGRATIONS_PATH=__inmem__ \
	LANGGRAPH_HTTP='{"app": "./tests/graphs/fastapi_jwt_middleware_ordering.py:app", "middleware_order": "$(1)", "enable_custom_route_auth": $(2)}' \
	uv run pytest -v $(AUTH_TEST)
endef

test-auth-fastapi-jwt--before-custom-middleware--no-custom-route-auth:
	$(call FASTAPI_JWT_AUTH_TEST,auth_first,false)

test-auth-fastapi-jwt--after-custom-middleware--no-custom-route-auth:
	$(call FASTAPI_JWT_AUTH_TEST,middleware_first,false)

test-auth-fastapi-jwt--before-custom-middleware--custom-route-auth:
	$(call FASTAPI_JWT_AUTH_TEST,auth_first,true)

test-auth-fastapi-jwt--after-custom-middleware--custom-route-auth:
	$(call FASTAPI_JWT_AUTH_TEST,middleware_first, true)


test-auth-watch:
	LANGGRAPH_RUNTIME_EDITION=inmem LANGGRAPH_AUTH='{"path": "./tests/graphs/fastapi_jwt_auth.py:get_current_active_user"}' REDIS_URI=_FAKE DATABASE_URI=:memory: MIGRATIONS_PATH=__inmem__ uv run ptw . -- -x -vv --ff --capture=no $(AUTH_TEST)

# dev commands

start:
	@if [ "$(FF_USE_CORE_API)" = "true" ]; then \
		$(MAKE) build-go-server && $(MAKE) start-go-server; \
		trap '$(MAKE) stop-go-server' INT TERM EXIT; \
	fi; \
	sleep 3 && \
	LANGGRAPH_HTTP='$(HTTP_CONFIG)' \
	LANGGRAPH_RUNTIME_EDITION=inmem \
	LANGGRAPH_AES_KEY='$(LANGGRAPH_AES_KEY)' \
	N_JOBS_PER_WORKER=2 \
	LANGSERVE_GRAPHS=$(LANGSERVE_GRAPHS_ALL) \
	LANGGRAPH_STORE='$(STORE_CONFIG)' \
	LANGGRAPH_CONFIG='{"agent": {"configurable": {"model_name": "openai"}}}' \
	LANGSMITH_LANGGRAPH_API_VARIANT=test \
	FF_USE_CORE_API=$(FF_USE_CORE_API) \
	BG_JOB_TIMEOUT_SECS=$(BG_JOB_TIMEOUT_SECS) \
	REDIS_URI=fake \
	DATABASE_URI=:memory: \
	MIGRATIONS_PATH=__inmem \
	uv run uvicorn \
		"langgraph_api.server:app" \
		--reload \
		--port 9123 \
		--reload-dir langgraph_api \
		--reload-dir ../runtime_inmem \
		--no-access-log


start-license-oss: start

start-encrypt:
	LANGGRAPH_HTTP='$(HTTP_CONFIG)' \
	LANGGRAPH_RUNTIME_EDITION=inmem \
	LANGGRAPH_AES_KEY='$(LANGGRAPH_AES_KEY)' \
	N_JOBS_PER_WORKER=2 \
	LANGSERVE_GRAPHS=$(LANGSERVE_GRAPHS_ALL) \
	LANGGRAPH_STORE='$(STORE_CONFIG)' \
	LANGGRAPH_ENCRYPTION='{"path": "./tests/graphs/custom_encryption.py:encryption"}' \
	LANGGRAPH_CONFIG='{"agent": {"configurable": {"model_name": "openai"}}}' \
	LANGSMITH_LANGGRAPH_API_VARIANT=test \
	BG_JOB_TIMEOUT_SECS=$(BG_JOB_TIMEOUT_SECS) \
	REDIS_URI=fake \
	DATABASE_URI=:memory: \
	MIGRATIONS_PATH=__inmem \
	uv run uvicorn \
		"langgraph_api.server:app" \
		--reload \
		--port 9123 \
		--reload-dir langgraph_api \
		--reload-dir ../runtime_inmem \
		--no-access-log


start-auth-jwt:
	LANGGRAPH_RUNTIME_EDITION=inmem LANGGRAPH_HTTP='$(HTTP_CONFIG)' \
	LANGGRAPH_AES_KEY='$(LANGGRAPH_AES_KEY)' \
	N_JOBS_PER_WORKER=2 \
	LANGSERVE_GRAPHS=$(LANGSERVE_GRAPHS_AUTH) \
	LANGGRAPH_STORE='$(STORE_CONFIG)' \
	LANGGRAPH_AUTH='{"path": "tests/graphs/jwt_auth.py:auth"}' \
	LANGSMITH_LANGGRAPH_API_VARIANT=test \
	REDIS_URI=fake \
	DATABASE_URI=:memory: \
	MIGRATIONS_PATH=__inmem \
	uv run uvicorn \
		"langgraph_api.server:app" \
		--reload \
		--port 9123 \
		--reload-dir langgraph_api \
		--reload-dir ../runtime_inmem \
		--no-access-log

start-auth-fastapi-jwt:
	LANGGRAPH_RUNTIME_EDITION=inmem LANGGRAPH_HTTP='$(HTTP_CONFIG)' \
	N_JOBS_PER_WORKER=2 \
	LANGSERVE_GRAPHS=$(LANGSERVE_GRAPHS_AUTH) \
	LANGGRAPH_STORE='$(STORE_CONFIG)' \
	LANGGRAPH_AUTH='{"path": "./tests/graphs/fastapi_jwt_auth.py:auth"}' \
	LANGSMITH_LANGGRAPH_API_VARIANT=test \
	REDIS_URI=fake \
	DATABASE_URI=:memory: \
	MIGRATIONS_PATH=__inmem \
	uv run uvicorn \
		"langgraph_api.server:app" \
		--reload \
		--port 9123 \
		--reload-dir langgraph_api \
		--reload-dir ../runtime_inmem \
		--no-access-log

define RUN_FASTAPI_JWT_MW_ORDERING
	LANGGRAPH_RUNTIME_EDITION=inmem \
	LANGGRAPH_HTTP='{"app": "./tests/graphs/fastapi_jwt_middleware_ordering.py:app", "middleware_order": "$(1)", "enable_custom_route_auth": $(2)}' \
	N_JOBS_PER_WORKER=2 \
	LANGSERVE_GRAPHS=$(LANGSERVE_GRAPHS_AUTH) \
	LANGGRAPH_STORE='$(STORE_CONFIG)' \
	LANGGRAPH_AUTH='{"path": "./tests/graphs/fastapi_jwt_middleware_ordering.py:auth"}' \
	LANGSMITH_LANGGRAPH_API_VARIANT=test \
	REDIS_URI=fake \
	DATABASE_URI=:memory: \
	MIGRATIONS_PATH=__inmem \
	uv run uvicorn \
		"langgraph_api.server:app" \
		--reload \
		--port 9123 \
		--reload-dir langgraph_api \
		--reload-dir ../runtime_inmem \
		--no-access-log
endef

start-auth-fastapi-jwt--before-custom-middleware--no-custom-route-auth:
	$(call RUN_FASTAPI_JWT_MW_ORDERING,auth_first,false)

start-auth-fastapi-jwt--after-custom-middleware--no-custom-route-auth:
	$(call RUN_FASTAPI_JWT_MW_ORDERING,middleware_first,false)

start-auth-fastapi-jwt--before-custom-middleware--custom-route-auth:
	$(call RUN_FASTAPI_JWT_MW_ORDERING,auth_first,true)

start-auth-fastapi-jwt--after-custom-middleware--custom-route-auth:
	$(call RUN_FASTAPI_JWT_MW_ORDERING,middleware_first,true)


start-js-server:
	@echo "Building and starting Go gRPC server..."
	$(MAKE) build-go-server
	$(MAKE) start-go-server
	@trap '$(MAKE) -C $(CURDIR) stop-go-server' INT TERM EXIT; \
	echo "Installing JS server dependencies..."; \
	cd ../public-api-server-js && yarn install; \
	echo "Building JS server..."; \
	cd ../public-api-server-js && yarn run build; \
	echo "Starting JS server on port 9123..."; \
	cd ../public-api-server-js && FF_USE_CORE_API=true \
	LANGSERVE_GRAPHS=$(LANGSERVE_GRAPHS_ALL) \
	LANGGRAPH_CONFIG='{"agent": {"configurable": {"model_name": "openai"}}}' \
	FF_USE_JS_API=true \
	PORT=9123 yarn start

VERSION_KIND ?= patch

bump-version:
	uv run --with hatch hatch version $(VERSION_KIND)
