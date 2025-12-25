
.PHONY: setup setup11 pydeps test bench-ci bench test-integration test-all coverage-report
.PHONY: test-resetup lint fix docs kind kind-teardown kuberay kuberay11 notebook
.PHONY: test-integration-gcp test-integration-aws test-stress-gcp
.PHONY: test-e2e-oxford-pets-gcp test-e2e-oxford-pets-aws test-e2e-openvid-gcp test-e2e-openvid-aws test-e2e-document-embedding-gcp test-e2e-document-embedding-aws test-e2e-gcp test-e2e-aws
.PHONY: dry-run-simple dry-run-openclip dry-run-blip dry-run-sentence-transformers dry-run-all
.PHONY: dry-run-openvid-simple dry-run-openvid-embedding-vjepa2 dry-run-openvid-all
.PHONY: dry-run-document-embedding

setup: kind-teardown kuberay pydeps

setup11: kind-teardown kuberay11 pydeps

pydeps:
	uv sync --all-groups --all-extras --locked

upgrade-pydeps:
	uv sync --all-groups --all-extras

# Ray 2.47+ is known to have some issues with uv.  ray workers would start up
# with no ray library available and hang unit tests.  A workaround is set
# RAY_ENABLE_UV_RUN_RUNTIME_ENV=0.   See this for details:
# https://github.com/ray-project/ray/issues/53848#issuecomment-3056271943

# all unit tests
test:
	RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest src/tests --cov=src/geneva --cov-report=term-missing --durations=0

# slow unit tests with local ray
test-ray:
	RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest src/tests -m "ray" --cov=src/geneva --cov-report=term-missing --durations=0

# fast unit tests (no ray)
test-fast:
	RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest src/tests -m "not ray and not slow" --cov=src/geneva --cov-report=term-missing --durations=0 -n auto

test-flaky:
	# only run flaky tests (currently multibackfill tests)
	RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest src/tests --cov=src/geneva -m "multibackfill or limit" --cov-report=term-missing  --durations=0

test-no-flaky:
	RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest src/tests --cov=src/geneva -m "not multibackfill and not limit" --cov-report=term-missing --durations=0

bench-ci:
	RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest src/benches -rx --cov=src/geneva --cov-append -v --benchmark-disable

bench:
	RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest src/benches -v --benchmark-compare --benchmark-autosave --benchmark-save-data --benchmark-group-by=name --benchmark-verbose -s

test-integration-gcp:
	uv run -m pytest src/integ_tests --csp=gcp --test-slug=$(SLUG) $(if $(BUCKET_PATH),--bucket-path=$(BUCKET_PATH)) --cov=src/geneva --cov-append -v -s --cov-report=term-missing --durations=0

test-integration-aws:
	uv run -m pytest src/integ_tests --csp=aws --test-slug=$(SLUG) $(if $(BUCKET_PATH),--bucket-path=$(BUCKET_PATH)) --cov=src/geneva --cov-append -v -s --cov-report=term-missing --durations=0

test-stress-gcp:
	uv run -m pytest src/stress_tests --csp=gcp --test-slug=$(SLUG) $(if $(BUCKET_PATH),--bucket-path=$(BUCKET_PATH)) --cov=src/geneva --cov-append -v -s --cov-report=term-missing -m "not xfail" --durations=0

test-stress-gcp-full:
	uv run -m pytest src/stress_tests --csp=gcp --test-slug=$(SLUG) $(if $(BUCKET_PATH),--bucket-path=$(BUCKET_PATH)) --cov=src/geneva --cov-append -v -s --cov-report=term-missing --durations=0

# E2E Tests - Oxford Pets Suite
# Note: Manifest upload and column addition happens automatically via pytest fixture
# Variables:
#   SKIP_GPU=1 to skip GPU tests (e.g., BLIP captions), default is to run GPU tests
#   TEST_FILES=<space-separated-list> (optional) - specific test files to run (e.g., "test_drivers/test_cpu_simple.py test_drivers/test_embeddings_openclip.py")
#   NUM_IMAGES=<number> (optional) - number of images to process, default 100
#   BATCH_SIZE=<number> (optional) - batch size for backfill operations, default 4
NUM_IMAGES ?= 100
BATCH_SIZE ?= 4
NUM_DOCS ?= 20

test-e2e-oxford-pets-gcp:
	cd e2e/oxford-pets && uv run -m pytest $(if $(TEST_FILES),$(TEST_FILES),test_drivers) --csp=gcp --test-slug=$(SLUG) --num-images=$(NUM_IMAGES) --batch-size=$(BATCH_SIZE) $(if $(SKIP_GPU),--skip-gpu) --cov=../../src/geneva --cov-append -v -s --cov-report=term-missing --durations=0

test-e2e-oxford-pets-aws:
	cd e2e/oxford-pets && uv run -m pytest test_drivers --csp=aws --test-slug=$(SLUG) --num-images=$(NUM_IMAGES) --batch-size=$(BATCH_SIZE) $(if $(SKIP_GPU),--skip-gpu) --cov=../../src/geneva --cov-append -v -s --cov-report=term-missing --durations=0

# E2E Tests - OpenVid Suite
# Note: Manifest upload and column addition happens automatically via pytest fixture
# Variables:
#   SKIP_GPU=1 to skip GPU tests, default is to run GPU tests
#   TEST_FILES=<space-separated-list> (optional) - specific test files to run
#   NUM_VIDEOS=<number> (optional) - number of videos to process, default 20
#   BATCH_SIZE=<number> (optional) - batch size for backfill operations (shared with oxford-pets), default 4
NUM_VIDEOS ?= 20

test-e2e-openvid-gcp:
	cd e2e/openvid && uv run -m pytest $(if $(TEST_FILES),$(TEST_FILES),test_drivers) --csp=gcp --test-slug=$(SLUG) --num-videos=$(NUM_VIDEOS) --batch-size=$(BATCH_SIZE) $(if $(SKIP_GPU),--skip-gpu) --cov=../../src/geneva --cov-append -v -s --cov-report=term-missing --durations=0

test-e2e-openvid-aws:
	cd e2e/openvid && uv run -m pytest test_drivers --csp=aws --test-slug=$(SLUG) --num-videos=$(NUM_VIDEOS) --batch-size=$(BATCH_SIZE) $(if $(SKIP_GPU),--skip-gpu) --cov=../../src/geneva --cov-append -v -s --cov-report=term-missing --durations=0

# E2E Tests - Document Embedding Suite
# Variables:
#   TEST_FILES=<space-separated-list> (optional) - specific test files to run
#   NUM_DOCS=<number> (optional) - number of documents to process, default 20
#   BATCH_SIZE=<number> (optional) - batch size for backfill operations, default 4
test-e2e-document-embedding-gcp:
	cd e2e/document_embedding && uv run -m pytest $(if $(TEST_FILES),$(TEST_FILES),test_drivers) --csp=gcp --test-slug=$(SLUG) --num-docs=$(NUM_DOCS) --batch-size=$(BATCH_SIZE) --cov=../../src/geneva --cov-append -v -s --cov-report=term-missing --durations=0

test-e2e-document-embedding-aws:
	cd e2e/document_embedding && uv run -m pytest test_drivers --csp=aws --test-slug=$(SLUG) --num-docs=$(NUM_DOCS) --batch-size=$(BATCH_SIZE) --cov=../../src/geneva --cov-append -v -s --cov-report=term-missing --durations=0

# E2E Tests - Convenience targets
test-e2e-gcp: test-e2e-oxford-pets-gcp test-e2e-openvid-gcp test-e2e-document-embedding-gcp

test-e2e-aws: test-e2e-oxford-pets-aws test-e2e-openvid-aws test-e2e-document-embedding-aws

# E2E Tests - Manifest Dry Run (local testing)
# Test manifest creation locally without uploading to GCS/S3
# Shows what paths and dependencies would be packaged
dry-run-simple:
	cd e2e/oxford-pets/udfs/simple && uv sync && uv run python upload_manifest.py --bucket gs://dummy --dry-run --verbose --generate-zip

dry-run-openclip:
	cd e2e/oxford-pets/udfs/openclip && uv sync && uv run python upload_manifest.py --bucket gs://dummy --dry-run  --verbose  --generate-zip

dry-run-blip:
	cd e2e/oxford-pets/udfs/blip && uv sync && uv run python upload_manifest.py --bucket gs://dummy --dry-run  --verbose  --generate-zip

dry-run-sentence-transformers:
	cd e2e/oxford-pets/udfs/sentence-transformers && uv sync && uv run python upload_manifest.py --bucket gs://dummy --dry-run  --verbose  --generate-zip

dry-run-all: dry-run-simple dry-run-openclip dry-run-blip dry-run-sentence-transformers

# E2E Tests - OpenVid Manifest Dry Run (local testing)
# Test manifest creation locally without uploading to GCS/S3
dry-run-openvid-simple:
	cd e2e/openvid/udfs/simple && uv sync && uv run python upload_manifest.py --bucket gs://dummy --dry-run --verbose --generate-zip

dry-run-openvid-embedding-vjepa2:
	cd e2e/openvid/udfs/embedding_vjepa2 && uv sync && uv run python upload_manifest.py --bucket gs://dummy --dry-run --verbose --generate-zip

dry-run-openvid-all: dry-run-openvid-simple dry-run-openvid-embedding-vjepa2

dry-run-document-embedding:
	cd e2e/document_embedding/udfs/pdf_embedding && uv sync && uv run python upload_manifest.py --bucket gs://dummy --dry-run --verbose --generate-zip

test-all: test test-integration-gcp test-integration-aws

coverage-report:
	uv run coverage xml

test-resetup: setup test

lint:
	uv run ruff format --check src
	uv run ruff check src
	uv run pyright

fix:
	uv run ruff format src
	uv run ruff check --fix src
	uv run pyright

docs:
	# uv sync --extra docs # this blows up other dependencies / e.g. notebooks
	cd docs ; uv run mkdocs serve

kind:
	tools/setup_kind_cluster.sh

kind-teardown:
	kind delete cluster --name geneva

kuberay: kind
	tools/setup_kuberay.sh

kuberay11: kind
	KUBERAY_VERSION=1.1.0 tools/setup_kuberay.sh

notebook:
	uv pip install ipykernel ipywidgets
	uv run jupyter-notebook --ip=0.0.0.0
