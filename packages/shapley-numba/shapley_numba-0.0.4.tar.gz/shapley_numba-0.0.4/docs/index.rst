shapley_numba
=============

**Numba-based computations for cooperative games.**

shapley_numba is a high-performance Python library for computing Shapley values and Harsanyi dividends
in cooperative game theory. It leverages :ref:`Numba's JIT compilation <concepts:numba-game>` to achieve fast computations even
for games with many players.

Features
--------

- **Fast exact Shapley calculation** - Optimized implementations using :doc:`Numba <concepts>`
- **Shapley Monte Carlo approximation** - For large-scale games
- **Harsanyi Dividends (synergies) computation** - Analyze player interactions
- **Set iteration tools** - Efficient subset enumeration utilities

Installation
------------

Using pip::

    pip install --index-url https://gitlab.com/api/v4/groups/shapley-numba/-/packages/pypi/simple shapley-numba

Using uv::

    uv add --index-url https://gitlab.com/api/v4/groups/shapley-numba/-/packages/pypi/simple shapley-numba

Quick Example
-------------

.. code-block:: python

    from shapley_numba.shapley import shapley
    from shapley_numba.examples import GloveGame

    glove_game = GloveGame(num_left_gloves=1)
    shapley(glove_game, num_players=3)

See :py:func:`shapley_numba.shapley.shapley` and :py:class:`shapley_numba.examples.GloveGame` for more details.

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   README

.. toctree::
   :maxdepth: 2
   :caption: Concepts

   concepts

.. toctree::
   :maxdepth: 2
   :caption: Notebooks

   notebooks

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   reference/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
