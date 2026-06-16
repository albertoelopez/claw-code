# CC2 board generation

This checkout can build the Claw Code 2.0 execution board with one command:

```bash
python3 scripts/build_cc2_board.py
```

The wrapper performs two steps:

1. Reconstructs a local CC2 source bundle with live GitHub data.
2. Runs the canonical board generator with `CC2_SOURCE_OMX` pointed at that reconstructed bundle.

Default outputs:

- Reconstructed source bundle: `.omx/reconstructed-source/`
- Board JSON: `.omx/cc2/board.json`
- Board Markdown: `.omx/cc2/board.md`

The reconstructed source bundle is intentionally marked as non-frozen evidence. Use it for local board generation and triage, not as a replacement for the original approved frozen source bundle.

Useful custom paths:

```bash
python3 scripts/build_cc2_board.py \
  --source-root /tmp/cc2-reconstructed-source/.omx \
  --out-dir /tmp/cc2-board
```

The command prints the generated board paths, total item count, and roadmap coverage counts after generation.

Verification commands:

```bash
python3 -m unittest tests.test_cc2_board_wrapper -v
python3 -m unittest discover -s tests -v
```
