install:
	python3 -m pip install '.[dev]'

test:
	python3 -m pytest

lint:
	python3 -m ruff check sentinel tests

serve:
	python3 -m sentinel.api

scan-reentrancy:
	sentinel scan ./examples/vulnerable_reentrancy --mock

scan-access-control:
	sentinel scan ./examples/vulnerable_access_control --mock
