
"""
Simple function to generate a time series using the Logistic map.
"""

import numpy as np
from ..optionalNJIT import optional_njit
from ..warningHandling import warnUser


@optional_njit( cache=True, nogil=True )   
def logistic( tsLen: int = 1000, skip: int = 100, x: float = 0.01, \
              r: float = 4.0, randomInit: bool = False) -> np.ndarray :
    
    """
    Generate a time series using the Logistic map.
    The Logistic map is defined as:
    .. math:: x_{n+1} = r * x_n * (1 - x_n)
    where :math:`x_n` is the value at time step :math:`n`, and :math:`r` is a parameter.

    Parameters
    ----------
    tsLen : int
        Length of the time series to generate.
    skip : int
        Number of initial iterations to skip.
    x : float
        Initial value of the time series.
    r : float
        Parameter of the Logistic map.
    randomInit : bool
        If True, a random initial value is generated between 0.01 and 0.99.
        
    Returns
    -------
    np.ndarray
        Generated time series.
    """

    if randomInit:
        x = np.random.uniform( 0.01, 0.99 )

    if x < 0.0 or x > 1.:
        warnUser( "TimeSeriesGeneration.Logistic.logistic", \
                  "x should be between 0.0 and 1.0" )
    if r < 0.0 or r > 4.:
        warnUser( "TimeSeriesGeneration.Logistic.logistic", \
                  "r should be between 0.0 and 4.0" )
        
    if tsLen < 1:
        raise ValueError( "tsLen must be greater than 0" )
    if skip < 0:
        raise ValueError( "skip must be greater than or equal to 0" )

    for t in range( skip ):
        x = r * x * ( 1.0 - x )

    TS = np.zeros( (tsLen) )
                                          
    for t in range( tsLen ):
        x = r * x * ( 1.0 - x )
        TS[t] = x

    return TS
