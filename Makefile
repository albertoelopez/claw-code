.PHONY: cc2-board test verify rust-verify

cc2-board:
	python3 scripts/build_cc2_board.py

test:
	python3 -m unittest discover -s tests -v

rust-verify:
	cd rust && ../scripts/fmt.sh --check && cargo clippy --workspace --all-targets -- -D warnings

verify: test rust-verify
