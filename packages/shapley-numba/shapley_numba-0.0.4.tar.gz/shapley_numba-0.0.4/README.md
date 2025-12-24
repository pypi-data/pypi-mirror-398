# Shapley Numba

[![Pipeline Status](https://gitlab.com/shapley-numba/shapley-numba/badges/master/pipeline.svg)](https://gitlab.com/shapley-numba/shapley-numba/-/pipelines)
[![Coverage](https://gitlab.com/shapley-numba/shapley-numba/badges/master/coverage.svg)](https://gitlab.com/shapley-numba/shapley-numba/-/commits/master)
[![PyPI version](https://img.shields.io/pypi/v/shapley-numba.svg)](https://pypi.org/project/shapley-numba/)
[![Python Version](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)](https://www.python.org/)
[![License: MIT-0](https://img.shields.io/badge/License-MIT--0-blue.svg)](https://opensource.org/licenses/MIT-0)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://shapley-numba-f859eb.gitlab.io/
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![MyPy](https://img.shields.io/badge/mypy-checked-blue)](http://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://gitlab.com/shapley-numba/shapley-numba/-/graphs/master)

Numba-based computations for cooperative games.

## Installation

pip:
```bash
pip install shapley-numba
```

uv
```bash
uv add shapley-numba
```
## Dependencies

`shapley-numba` package depends only on `numba` and `numpy`.

## Features

- Fast exact Shapley calculation.
- Shapley Monte Carlo approximation.
- Harsanyi Dividends (synergies) computation.
- Set iteration tools.
- Game authoring tools and game templates.

## Quickstart

See [tutorial notebook](https://shapley-numba-f859eb.gitlab.io/01%20sample_notebook.html) for quick start.


## Usage

This package is intended to compute quantities associated with cooperative games. Currently we want to implement two functions:

1. Shapley values
2. Harsanyi dividends, also called synergies.


This package also provides tools to author and modify cooperative games, such as game templates.

A game is a class that implements `value` method. The `value` method should accept a numpy array of zeros and ones indicating membership of each element in the subset.

The intended use of the package is for games where each computation of `value` is relatively cheap. This allows to speed up such computations using numba.

For optimal performance, the game should be written so that it can be compiled using `numba.experimental.jitclass` compiler. That way, numba compiled functions can be applied. Otherwise, a python fallback will be applied.

The basic usage is as follows:

```python
from shapley_numba.shapley import shapley
from shapley_numba.examples import GloveGame
glove_game = GloveGame(num_left_gloves=1)
shapley(glove_game, num_players=3)
```

See [documentation](https://shapley-numba-f859eb.gitlab.io/) for detailed reference.


# Credits

Dimitry Offengenden participated in development of this code and contributed several game examples.

This code was developed with assistance from Google Gemini Code Assist (version 2.52.0).

This code was developed with assistance from Claude Code.


# Alternatives

- [SHAP](https://shap.readthedocs.io/) applies Shapley values to machine learning models but can be used in conjunction with any game.
