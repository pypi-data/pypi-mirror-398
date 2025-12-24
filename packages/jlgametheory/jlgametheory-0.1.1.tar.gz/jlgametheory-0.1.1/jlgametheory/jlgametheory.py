import numpy as np
from . import GameTheory


def to_jl_nfg(g):
    g_jl = GameTheory.NormalFormGame(
        *(GameTheory.Player(player.payoff_array) for player in g.players)
    )
    return g_jl


def _to_py_ne(NE_jl):
    return tuple(x.to_numpy() for x in NE_jl)


def _to_py_nes(NEs_jl):
    return [_to_py_ne(NE) for NE in NEs_jl]


def lrsnash(g):
    """
    Compute in exact arithmetic all extreme mixed-action Nash equilibria
    of a 2-player normal form game with integer payoffs. This function
    calls the Nash equilibrium computation routine in `lrslib` (through
    its Julia wrapper `LRSLib.jl`) which is based on the "lexicographic
    reverse search" vertex enumeration algorithm [1]_.

    Parameters
    ----------
    g : NormalFormGame
        2-player NormalFormGame instance with integer payoffs.

    Returns
    -------
    NEs : list(tuple(ndarray(object, ndim=1)))
        List containing tuples of Nash equilibrium mixed actions, where
        the values are represented by `fractions.Fraction`.

    Examples
    --------
    A degenerate game example:

    >>> import quantecon.game_theory as gt
    >>> import jlgametheory as jgt
    >>> from pprint import pprint
    >>> bimatrix = [[(3, 3), (3, 3)],
    ...             [(2, 2), (5, 6)],
    ...             [(0, 3), (6, 1)]]
    >>> g = gt.NormalFormGame(bimatrix)
    >>> NEs = jgt.lrsnash(g)
    >>> pprint(NEs)
    [(array([Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)], dtype=object),
      array([Fraction(1, 1), Fraction(0, 1)], dtype=object)),
     (array([Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)], dtype=object),
      array([Fraction(2, 3), Fraction(1, 3)], dtype=object)),
     (array([Fraction(0, 1), Fraction(1, 3), Fraction(2, 3)], dtype=object),
      array([Fraction(1, 3), Fraction(2, 3)], dtype=object))]

    The set of Nash equilibria of this degenerate game consists of an
    isolated equilibrium, the third output, and a non-singleton
    equilibrium component, the extreme points of which are given by the
    first two outputs.

    References
    ----------
    .. [1] D. Avis, G. Rosenberg, R. Savani, and B. von Stengel,
       "Enumeration of Nash Equilibria for Two-Player Games," Economic
       Theory (2010), 9-37.

    """
    try:
        N = g.N
    except AttributeError:
        raise TypeError('input must be a 2-player NormalFormGame')
    if N != 2:
        raise NotImplementedError('Implemented only for 2-player games')
    if not np.issubdtype(g.dtype, np.integer):
        raise NotImplementedError(
            'Implemented only for games with integer payoffs'
        )

    NEs_jl = GameTheory.lrsnash(to_jl_nfg(g))
    return _to_py_nes(NEs_jl)


def hc_solve(g, ntofind=float('inf'), **options):
    """
    Compute all isolated mixed-action Nash equilibria of an N-player
    normal form game.

    This function solves a system of polynomial equations arising from
    the nonlinear complementarity problem representation of Nash
    equilibrium, by using `HomotopyContinuation.jl`.

    Parameters
    ----------
    g : NormalFormGame
        N-player NormalFormGame instance.

    ntofind : scalar, optional(default=float('inf'))
        Number of Nash equilibria to find.

    options :
        Optional keyword arguments to pass to `HomotopyContinuation.solve`.
        For example, the option `seed` can set the random seed used
        during the computations. See the `documentation
        <https://www.juliahomotopycontinuation.org/HomotopyContinuation.jl/stable/solve/>`_
        for `HomotopyContinuation.solve` for details.

    Returns
    -------
    NEs : list(tuple(ndarray(float, ndim=1)))
        List containing tuples of Nash equilibrium mixed actions.

    Examples
    --------
    Consider the 3-player 2-action game with 9 Nash equilibria in
    McKelvey and McLennan (1996) "Computation of Equilibria in Finite
    Games":

    >>> import quantecon.game_theory as gt
    >>> import jlgametheory as jgt
    >>> from pprint import pprint
    >>> import numpy as np
    >>> np.set_printoptions(precision=3)  # Reduce the digits printed
    >>> g = gt.NormalFormGame((2, 2, 2))
    >>> g[0, 0, 0] = 9, 8, 12
    >>> g[1, 1, 0] = 9, 8, 2
    >>> g[0, 1, 1] = 3, 4, 6
    >>> g[1, 0, 1] = 3, 4, 4
    >>> print(g)
    3-player NormalFormGame with payoff profile array:
    [[[[ 9.,  8., 12.],   [ 0.,  0.,  0.]],
      [[ 0.,  0.,  0.],   [ 3.,  4.,  6.]]],
    <BLANKLINE>
     [[[ 0.,  0.,  0.],   [ 3.,  4.,  4.]],
      [[ 9.,  8.,  2.],   [ 0.,  0.,  0.]]]]
    >>> NEs = jgt.hc_solve(g, show_progress=False)
    >>> len(NEs)
    9
    >>> pprint(NEs)
    [(array([0., 1.]), array([0., 1.]), array([1., 0.])),
     (array([0.5, 0.5]), array([0.5, 0.5]), array([1.000e+00, 2.351e-38])),
     (array([1., 0.]), array([0., 1.]), array([-1.881e-37,  1.000e+00])),
     (array([0.25, 0.75]), array([0.5, 0.5]), array([0.333, 0.667])),
     (array([0.25, 0.75]), array([1.000e+00, 1.345e-43]), array([0.25, 0.75])),
     (array([0., 1.]), array([0.333, 0.667]), array([0.333, 0.667])),
     (array([1., 0.]), array([ 1.00e+00, -5.74e-42]), array([1., 0.])),
     (array([0., 1.]), array([1., 0.]), array([2.374e-66, 1.000e+00])),
     (array([0.5, 0.5]), array([0.333, 0.667]), array([0.25, 0.75]))]
    >>> all(g.is_nash(NE) for NE in NEs)
    True

    """
    try:
        N = g.N
    except AttributeError:
        raise TypeError('g must be a NormalFormGame')
    if N < 2:
        raise NotImplementedError('Not implemented for 1-player games')

    NEs_jl = GameTheory.hc_solve(to_jl_nfg(g), ntofind=ntofind, **options)
    return _to_py_nes(NEs_jl)
