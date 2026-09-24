PYTHON ?= .venv/bin/python
DVD_SOLC ?= $(HOME)/.solc-select/artifacts/solc-0.8.25/solc-0.8.25
FOUNDRY_BIN ?= $(HOME)/.foundry/bin
SECURITY_TOOLS_BIN ?= $(HOME)/.local/bin

install:
	$(PYTHON) -m pip install '.[dev,llm]'

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check sentinel tests

serve:
	$(PYTHON) -m sentinel.api

scan-reentrancy:
	$(PYTHON) -m sentinel.cli scan ./examples/vulnerable_reentrancy --mock

scan-access-control:
	$(PYTHON) -m sentinel.cli scan ./examples/vulnerable_access_control --mock

scan-tx-origin:
	$(PYTHON) -m sentinel.cli scan ./examples/vulnerable_tx_origin --mock

scan-unchecked-call:
	$(PYTHON) -m sentinel.cli scan ./examples/vulnerable_unchecked_call --mock

prepare-damn-vulnerable-defi:
	@test -x "$(DVD_SOLC)" || (echo "Solidity 0.8.25 is required: run 'solc-select install 0.8.25 && solc-select use 0.8.25', or set DVD_SOLC=/path/to/solc"; exit 1)
	mkdir -p datasets/damn-vulnerable-defi/.sentinel-bin
	ln -sfn "$(DVD_SOLC)" datasets/damn-vulnerable-defi/.sentinel-bin/solc

test-damn-vulnerable-defi: prepare-damn-vulnerable-defi
	cd datasets/damn-vulnerable-defi && PATH="$$PWD/.sentinel-bin:$(FOUNDRY_BIN):$$PATH" forge build

# Damn Vulnerable DeFi intentionally ships unsolved challenge tests. This target
# demonstrates those expected failures; it is not a Sentinel health check.
test-damn-vulnerable-defi-challenges: prepare-damn-vulnerable-defi
	cd datasets/damn-vulnerable-defi && PATH="$$PWD/.sentinel-bin:$(FOUNDRY_BIN):$$PATH" forge test

scan-damn-vulnerable-defi: prepare-damn-vulnerable-defi
	PATH="$(CURDIR)/datasets/damn-vulnerable-defi/.sentinel-bin:$(FOUNDRY_BIN):$(SECURITY_TOOLS_BIN):$$PATH" SOLC_BINARY="$(CURDIR)/datasets/damn-vulnerable-defi/.sentinel-bin/solc" MYTHRIL_MAX_SOURCES=1 MYTHRIL_EXECUTION_TIMEOUT_SECONDS=20 $(PYTHON) -m sentinel.cli scan ./datasets/damn-vulnerable-defi --scout-only --output ./reports/damn-vulnerable-defi

# Runs one real scanner-selected candidate through the configured Red Team, Blue
# Team, and deterministic Forge Judge.  The report is authoritative: only
# a `verified` result produces a patched Solidity artifact.
run-damn-vulnerable-defi-agentic: prepare-damn-vulnerable-defi
	PATH="$(CURDIR)/datasets/damn-vulnerable-defi/.sentinel-bin:$(FOUNDRY_BIN):$(SECURITY_TOOLS_BIN):$$PATH" SOLC_BINARY="$(CURDIR)/datasets/damn-vulnerable-defi/.sentinel-bin/solc" MYTHRIL_MAX_SOURCES=1 MYTHRIL_EXECUTION_TIMEOUT_SECONDS=20 $(PYTHON) -m sentinel.cli scan ./datasets/damn-vulnerable-defi --max-retries 1 --output ./reports/damn-vulnerable-defi-agentic

prepare-forge-artifacts:
	$(PYTHON) scripts/prepare_forge_artifacts.py

benchmark-forge-artifacts: prepare-forge-artifacts
	PATH="$(SECURITY_TOOLS_BIN):$$PATH" $(PYTHON) scripts/benchmark_forge_artifacts.py --limit 10

benchmark-forge-artifacts-full: prepare-forge-artifacts
	PATH="$(SECURITY_TOOLS_BIN):$$PATH" $(PYTHON) scripts/benchmark_forge_artifacts.py --limit 500
