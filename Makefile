PYTHON ?= .venv/bin/python

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

download-smartbugs:
	git clone --depth 1 https://github.com/smartbugs/smartbugs-curated.git datasets/smartbugs-curated

prepare-smartbugs:
	$(PYTHON) scripts/prepare_smartbugs.py

scan-smartbugs:
	$(PYTHON) scripts/scan_smartbugs.py --limit 5

scan-smartbugs-all:
	$(PYTHON) scripts/scan_smartbugs.py --limit 0
