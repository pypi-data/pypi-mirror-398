# PyXindy (Python port of xindy)

[![GitHub issues](https://img.shields.io/github/issues/yves-chevallier/pyxindy.svg)](https://github.com/yves-chevallier/pyxindy/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/yves-chevallier/pyxindy.svg)](https://github.com/yves-chevallier/pyxindy/commits/main)
![CI](https://github.com/yves-chevallier/pyxindy/actions/workflows/ci.yml/badge.svg)
![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.13%20%7C%203.14-blue)
[![PyPI version](https://img.shields.io/pypi/v/pyxindy)](https://pypi.org/project/pyxindy/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pyxindy)](https://pypi.org/project/pyxindy/#files)
[![License](https://img.shields.io/pypi/l/pyxindy)](https://github.com/yves-chevallier/pyxindy/blob/main/LICENSE)
[![codecov](https://codecov.io/github/yves-chevallier/pyxindy/branch/main/graph/badge.svg)](https://codecov.io/github/yves-chevallier/pyxindy)

Python reimplementation of **xindy**, the flexible index processor originally written in CLISP. PyXindy aims to be a drop-in replacement where the original xindy is difficult to install or integrate (for example with Tectonic or minimal TeX setups).

![PyXindy](docs/assets/pyxindy.svg)

## Background and history

- **makeindex**: introduced in 1987 by Pehong Chen, bundled with TeX distributions through the late 1980s and 1990s as the default indexer for LaTeX. It remains widely available in TeX Live and MiKTeX.
- **xindy**: created in the mid-1990s (first public releases in 1996) by Joachim Schrod to handle multilingual indexing, flexible sort rules, and markup targets beyond TeX (SGML/HTML). Version 2.x has shipped with TeX Live since the early 2000s.

Together they form a decades-old toolchain; PyXindy keeps the mature behavior while modernizing the implementation and packaging.

## Why PyXindy port

1. Easier installation: pure-Python stack, no CLISP dependency, plays nicely with `uv`, `pip`, and containerized CI.
2. Better integration: Tectonic and other minimal TeX environments can use xindy-like features without installing a full TeX Live.
3. Maintainability: Python codebase lowers the barrier for contributors and makes testing/CI straightforward.
4. Extensibility: reuses the historical xindy modules/styles while making it simpler to experiment with new features or diagnostics.

## Usage

```bash
lualatex document.tex
uv run xindy -M path/to/style.xdy -o document.ind document.raw
lualatex document.tex
```

## Quick commands

- Generate an index from `.raw` with a `.xdy` style:

  ```bash
  uv run xindy-py -M path/to/style.xdy -o output.ind path/to/index.raw
  ```

- Convert a TeX `.idx` file to `.raw`:

  ```bash
  uv run texindy-py path/to/input.idx -o output.raw
  ```

- Use the makeindex-compatible interface:

  ```bash
  uv run makeindex-py path/to/input.idx -o output.ind -t output.ilg -c
  ```

## Entry points

- `xindy-py`: core processor; reads `.raw` plus `.xdy` style and renders the formatted index.
- `texindy-py`: TeX converter; turns `.idx` into `.raw` suitable for xindy processing.
- `makeindex-py`: makeindex-compatible wrapper layered on the xindy engine; accepts common `-c/-l/-o/-t` flags.
- `makeglossaries-py`: glossaries helper; inspects LaTeX `.aux` to drive `makeindex-py`/xindy for glossary files.

Historical xindy modules/styles (`vendor/xindy-2.1/modules`) are resolved automatically via `require`. The wrapper `makeindex-py` supports the usual `-l/-c/-o/-t` flags.

## xindy CLI

```bash
uv run xindy-py [-M style.xdy] [-o output.ind] [-L searchpath] [-C encoding] [-l logfile] [-t] input.raw
```

- `-M/--module/--style`: `.xdy` style to use (defaults to `<raw>.xdy`)
- `-o/--output`: output target (`stdout` if omitted)
- `-L/--searchpath`: extra search paths for `require` (merged with `XINDY_SEARCHPATH`)
- `-C/--codepage`: output encoding (default: utf-8)
- `-l/--log`: write a brief log file
- `-t/--trace`: show Python tracebacks on errors

## tex2xindy

```bash
uv run texindy-py input.idx -o output.raw --input-encoding latin-1 --output-encoding utf-8
```

- Handles hierarchies `!`, display `@`, encap `|`, basic TeX macros/escapes, crossrefs `see{target}` → `:xref`.
- Emits `:tkey` when the displayed form differs from the sort key.

## makeindex4

```bash
uv run makeindex-py input.idx -o output.ind -t output.ilg [-c] [-l]
```

- `-c`: compress spaces in keys (makeindex behavior)
- `-l`: ignore spaces for sorting (adds `sort-rule " " ""`)
- `--debug`: print tracebacks; otherwise errors are summarized and written to the `.ilg` log
- Generates a temporary style, detects attributes/crossrefs, loads `tex/makeidx4.xdy`.

## Examples

- Replay a historical fixture:

  ```bash
  uv run xindy-py -M vendor/xindy-2.1/tests/ex1.xdy \
        -o /tmp/ex1.ind vendor/xindy-2.1/tests/ex1.raw
  ```

- Chain `.idx → .ind` in one command:

  ```bash
  uv run makeindex-py vendor/xindy-2.1/tests/infII.idx -o /tmp/infII.ind
  ```

## Development

1. Create a virtual environment and install dependencies:

   ```bash
   uv sync --extra dev  # or: pip install -e .[dev]
   ```

2. Run tests and linters:

   ```bash
   uv run pytest
   uv run ruff check
   ```

3. Smoke-test the binary:

   ```bash
   python -m xindy --version
   ```

The roadmap is tracked in `PLAN.md`.
