install:
	python3 -m pip install -e '.[dev]'

test:
	python3 -m pytest

scan-reentrancy:
	sentinel scan ./examples/vulnerable_reentrancy --mock
