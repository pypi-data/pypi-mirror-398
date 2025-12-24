
"""
Simple function to generate a time series using the Henon map.
"""

import numpy as np
from ..optionalNJIT import optional_njit
from ..warningHandling import warnUser


@optional_njit( cache=True, nogil=True )   
def henon( tsLen: int = 1000, x: float = 0.5, y: float = 0.5, a: float = 1.4, b: float = 0.3, randomInit: bool = False ) -> np.ndarray :

    """
    Generate a time series using the Henon map.
    The Henon map is defined as:
    .. math:: x_{n+1} = 1 - a * x_n^2 + y_n
    .. math:: y_{n+1} = b * x_n
    where :math:`x_n` and :math:`y_n` are the values at time step :math:`n`, and :math:`a` and :math:`b` are parameters.
    
    Parameters
    ----------
    tsLen : int
        Length of the time series to generate.
    x : float
        Initial value of x.
    y : float
        Initial value of y.
    a : float
        Parameter a of the Henon map.
    b : float
        Parameter b of the Henon map.
    randomInit : bool
        If True, a random initial value is generated for x and y.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    if randomInit:
        x = np.random.uniform( -1., 1. )
        y = np.random.uniform( -0.3, 0.3 )

    if x < -1.5 or x > 1.5:
        warnUser( "TimeSeriesGeneration.Henon.henon", \
                  "x should be between -1.5 and 1.5" )
    if y < -0.5 or y > 0.5:
        warnUser( "TimeSeriesGeneration.Henon.henon", \
                  "y should be between -0.5 and 0.5" )

    if tsLen < 1:
        raise ValueError( "tsLen must be greater than 0" )

    TS = np.zeros( (tsLen, 2) )
    TS[0, 0] = x
    TS[0, 1] = y
                                          
    for i in range(1, tsLen):

        TS[i, 0] = 1.0 - a * TS[i - 1, 0] * TS[i - 1, 0] + TS[i - 1, 1]
        TS[i, 1] = b * TS[i - 1, 0]
    
    return TS

