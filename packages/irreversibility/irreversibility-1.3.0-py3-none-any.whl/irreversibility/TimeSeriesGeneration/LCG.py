
"""
Function to generate a time series using the linear congruential generator.
"""

import numpy as np
from ..optionalNJIT import optional_njit
from ..warningHandling import warnUser


@optional_njit( cache=True, nogil=True )   
def congruential( tsLen: int = 1000, x: float = 0.0, A: int = 7141, \
                  B: int = 54773, C: int = 259200, randomInit: bool = False ) -> np.ndarray :

    """
    Generate a time series using a linear congruential generator.
    
    Parameters
    ----------
    tsLen : int
        Length of the time series to generate.
    x : float
        Initial value of the time series.
    A : float
        Parameter A of the LCG.
    B : float
        Parameter B of the LCG.
    C : float
        Parameter C of the LCG.
    randomInit : bool
        If True, a random initial value is generated for x.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    if randomInit:
        x = np.random.uniform( 0, C )

    if tsLen < 1:
        raise ValueError( "tsLen must be greater than 0" )

    TS = np.zeros( ( tsLen ) )
    for k in range( 1, tsLen ):
        TS[ k ] = np.mod( A * TS[ k - 1 ] + B, C )
        
    TS /= C
    
    return TS

