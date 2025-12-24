# jlgametheory

[![Build Status](https://github.com/QuantEcon/jlgametheory/actions/workflows/ci.yml/badge.svg)](https://github.com/QuantEcon/jlgametheory/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/QuantEcon/jlgametheory/badge.svg)](https://coveralls.io/github/QuantEcon/jlgametheory)
[![Documentation (stable)](https://img.shields.io/badge/docs-stable-blue.svg)](https://quantecon.github.io/jlgametheory/stable/)
[![Documentation (latest)](https://img.shields.io/badge/docs-latest-blue.svg)](https://quantecon.github.io/jlgametheory/latest/)

Python interface to GameTheory.jl

`jlgametheory` is a Python package that allows passing
a `NormalFormGame` instance from
[`QuantEcon.py`](https://github.com/QuantEcon/QuantEcon.py) to
[`GameTheory.jl`](https://github.com/QuantEcon/GameTheory.jl) functions
via [`JuliaCall`](https://github.com/JuliaPy/PythonCall.jl).

## Installation

```
pip install jlgametheory
```

## Implemented functions

* [`lrsnash`](https://quantecon.github.io/jlgametheory/stable/_autosummary/jlgametheory.lrsnash.html):
  Compute in exact arithmetic all extreme mixed-action Nash equilibria of a 2-player normal form game with integer payoffs.
* [`hc_solve`](https://quantecon.github.io/jlgametheory/stable/_autosummary/jlgametheory.hc_solve.html):
  Compute all isolated mixed-action Nash equilibria of an N-player normal form game.

## Example usage

```python
import quantecon.game_theory as gt
import jlgametheory as jgt
```

### lrsnash

`lrsnash` calls the Nash equilibrium computation routine in [lrslib](http://cgm.cs.mcgill.ca/~avis/C/lrs.html)
(through its Julia wrapper [LRSLib.jl](https://github.com/JuliaPolyhedra/LRSLib.jl)):

```python
bimatrix = [[(3, 3), (3, 2)],
            [(2, 2), (5, 6)],
            [(0, 3), (6, 1)]]
g = gt.NormalFormGame(bimatrix)
jgt.lrsnash(g)
```

```
[(array([Fraction(4, 5), Fraction(1, 5), Fraction(0, 1)], dtype=object),
  array([Fraction(2, 3), Fraction(1, 3)], dtype=object)),
 (array([Fraction(0, 1), Fraction(1, 3), Fraction(2, 3)], dtype=object),
  array([Fraction(1, 3), Fraction(2, 3)], dtype=object)),
 (array([Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)], dtype=object),
  array([Fraction(1, 1), Fraction(0, 1)], dtype=object))]
```

### hc_solve

`hc_solve` computes all isolated Nash equilibria of an N-player game by using
[HomotopyContinuation.jl](https://github.com/JuliaHomotopyContinuation/HomotopyContinuation.jl):

```python
g = gt.NormalFormGame((2, 2, 2))
g[0, 0, 0] = 9, 8, 12
g[1, 1, 0] = 9, 8, 2
g[0, 1, 1] = 3, 4, 6
g[1, 0, 1] = 3, 4, 4
jgt.hc_solve(g)
```

```
[(array([0., 1.]), array([0., 1.]), array([1., 0.])),
 (array([0.5, 0.5]), array([0.5, 0.5]), array([1.000e+00, 2.351e-38])),
 (array([1., 0.]), array([0., 1.]), array([-1.881e-37,  1.000e+00])),
 (array([0.25, 0.75]), array([0.5, 0.5]), array([0.333, 0.667])),
 (array([0.25, 0.75]), array([1.000e+00, 1.345e-43]), array([0.25, 0.75])),
 (array([0., 1.]), array([0.333, 0.667]), array([0.333, 0.667])),
 (array([1., 0.]), array([ 1.00e+00, -5.74e-42]), array([1., 0.])),
 (array([0., 1.]), array([1., 0.]), array([2.374e-66, 1.000e+00])),
 (array([0.5, 0.5]), array([0.333, 0.667]), array([0.25, 0.75]))]
```

## Tutorials

* [Tools for Game Theory in QuantEcon.py](https://nbviewer.jupyter.org/github/QuantEcon/game-theory-notebooks/blob/main/game_theory_py.ipynb)
* [Tools for Game Theory in GameTheory.jl](https://nbviewer.jupyter.org/github/QuantEcon/game-theory-notebooks/blob/main/game_theory_jl.ipynb)
