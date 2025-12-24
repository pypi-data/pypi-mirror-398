
"""
Two variants of a synthetic model to generate time series that
are irreversible at specific time scales.

An explanation can be found in:

Zanin, M., & Papo, D. (2025).
Algorithmic Approaches for Assessing Multiscale Irreversibility in Time Series: Review and Comparison.
Entropy, 27(2), 126.
"""

import numpy as np
from ..optionalNJIT import optional_njit
from ..warningHandling import warnUser


@optional_njit( cache=True, nogil=True )   
def msmodel( tsLen: int = 1000, tau: int = 2, mu: float = 0.05, \
             randomInit: bool = False ) -> np.ndarray :

    """
    Generate a time series using a multiscale model. See:
    Zanin, M., & Papo, D. (2025). Algorithmic Approaches for Assessing Multiscale Irreversibility in Time Series: Review and Comparison. Entropy, 27(2), 126.

    Parameters
    ----------
    tsLen : int
        Length of the time series to generate.
    tau : int
        Time scale of the model.
    mu : float
        Shift with respect to the previous value.
    randomInit : bool
        Not used, kept for compatibility with other functions.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    if mu < 0.0 or mu > 1.:
        warnUser( "TimeSeriesGeneration.MSModel.msmodel", \
                  "mu should be between 0.0 and 1.0" )

    if tsLen < 1:
        raise ValueError( "tsLen must be greater than 0" )
    if tau < 1:
        raise ValueError( "tau must be greater than 0" )

    TS = np.zeros( ( tsLen ) )
                                          
    for i in range( 0, tsLen ):

        if np.mod( i, tau ) == 0:
            TS[ i ] = np.random.uniform( 0., 1. )
        else:
            TS[ i ] = np.mod( TS[ i - 1 ] - mu, 1.0 )
    
    return TS


@optional_njit( cache=True, nogil=True )   
def msmodel_periodic( tsLen: int = 1000, tau: int = 2, \
                      mu: float = 0.05, randomInit: bool = False ) \
                      -> np.ndarray :

    """
    Generate a time series using a multiscale model with periodicity. See:
    Zanin, M., & Papo, D. (2025). Algorithmic Approaches for Assessing Multiscale Irreversibility in Time Series: Review and Comparison. Entropy, 27(2), 126.

    Parameters
    ----------
    tsLen : int
        Length of the time series to generate.
    tau : int
        Time scale of the model.
    mu : float
        Shift with respect to the previous value.
    randomInit : bool
        Not used, kept for compatibility with other functions.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    if mu < 0.0 or mu > 1.:
        warnUser( "TimeSeriesGeneration.MSModel.msmodel_periodic", \
                  "mu should be between 0.0 and 1.0" )

    if tsLen < 1:
        raise ValueError( "tsLen must be greater than 0" )
    if tau < 1:
        raise ValueError( "tau must be greater than 0" )

    TS = np.zeros( ( tsLen ) )
                                          
    for i in range( 0, tsLen ):

        if np.mod( i, tau + 1 ) < tau:
            TS[ i ] = np.random.uniform( 0., 1. )
        else:
            TS[ i ] = np.mod( TS[ i - tau ] - mu, 1.0 )
    
    return TS

