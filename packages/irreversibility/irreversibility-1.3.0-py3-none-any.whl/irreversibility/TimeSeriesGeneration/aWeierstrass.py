
import numpy as np
from ..optionalNJIT import optional_njit
from ..warningHandling import warnUser


@optional_njit( cache=True, nogil=True )   
def ST( offset, period, w ):

    newOff = np.mod( offset, period ) / period

    refValuesX = [ 0.0, w, 1.0 ]
    refValuesY = [ 0.0, 1.0, 0.0 ]

    value = np.interp( newOff, refValuesX, refValuesY )
    return value



@optional_njit( cache=True, nogil=True )   
def aWeierstrass( tsLen: int = 1000, period: int = 100, \
                  numHarms: int = 50, w: float = 0.2 ) -> np.ndarray :
        
    """
    Generate a time series using the Weierstrass function. See:
    Burykin, A., Costa, M. D., Peng, C. K., Goldberger, A. L., & Buchman, T. G. (2011). Generating signals with multiscale time irreversibility: the asymmetric weierstrass function. Complexity, 16(4), 29-38.
    
    Parameters
    ----------
    tsLen : int
        Length of the time series to generate.
    period : int
        Period of the time series.
    numHarms : int
        Number of harmonics to include in the time series.
    w : float
        Asymmetry factor of all harmonics.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    if tsLen < 1:
        raise ValueError( "tsLen must be greater than 0" )
    if period < 1:
        raise ValueError( "period must be greater than 0" )
    if numHarms < 1:
        raise ValueError( "numHarms must be greater than 0" )
    if w < 0.0 or w > 1.0:
        raise ValueError( "w must be between 0.0 and 1.0" )

    TS = np.zeros( ( tsLen ) )

    for k in range( 1, numHarms + 1 ):

        tPeriod = period / k
        tAmpl = 1 / ( k / 2.0 )
        TS += ST( np.arange( tsLen ), tPeriod, w ) * tAmpl

    TS /= np.max( TS )

    return TS


