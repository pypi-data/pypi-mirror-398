
"""
Function to generate time series using a geometric Brownian motions with stochastic resetting (srGBM). Depending on the parameters, mainly the reset probability and the drift, resulting time series have a tuneable degree of irreversibility.

From:
    Stojkoski, V.; Sandev, T.; Kocarev, L.; Pal, A.
    Geometric Brownian motion under stochastic resetting: A stationary yet nonergodic process.
    Physical Review E 2021, 104, 014121.
"""

import numpy as np
from ..optionalNJIT import optional_njit
from ..warningHandling import warnUser


@optional_njit( cache=True, nogil=True )   
def srGBM( tsLen: int = 1000, drift: float = 0.05,
           noiseA: float = 0.01, r: float = 0.01 ):

    """
    Generate a time series using a geometric Brownian motion with stochastic resetting (srGBM).
    The srGBM is defined as:
    .. math:: x_{n+1} = x_n + \\mu x_n \Delta t + \\sigma x_n \\Delta W
    where :math:`x_n` is the value at time step :math:`n`, :math:`\\mu` is the drift, :math:`\\sigma` is the noise, and :math:`\\Delta W` is a Wiener process.
    The stochastic resetting is applied with a probability :math:`r` at each time step.
    
    Parameters
    ----------
    tsLen : int
        Length of the time series to generate.
    drift : float
        Drift of the geometric Brownian motion.
    noiseA : float
        Noise amplitude of the geometric Brownian motion.
    r : float
        Reset probability of the stochastic resetting.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    if tsLen < 1:
        raise ValueError( "tsLen must be greater than 0" )
    if r < 0.0 or r > 1.0:
        warnUser( "TimeSeriesGeneration.srGBM.srGBM", \
                  "r should be between 0.0 and 1.0" )

    TS = np.zeros( ( tsLen ) )
    TS[ 0 ] = 1.
    deltaT = 1.

    for t in range( 1, tsLen ):

        if np.random.uniform( 0., 1. ) < r * deltaT:
            TS[ t ] = 1.0
            continue

        TS[ t ] = TS[ t - 1 ]
        TS[ t ] += TS[ t - 1 ] * ( drift + np.sqrt( deltaT ) * noiseA * np.random.normal( 0.0, 1.0 ) )

    return TS

