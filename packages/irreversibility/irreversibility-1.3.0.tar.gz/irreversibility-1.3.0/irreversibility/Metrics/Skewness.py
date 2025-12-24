
"""
Skewness test

From:
    Koutsoyiannis, D. (2019)
    Time's arrow in stochastic characterization and simulation of atmospheric and hydrological processes.
    Hydrol. Sci. J. (64), 1013-1037.
    
    Vavoulogiannis, S., Iliopoulou, T., Dimitriadis, P., & Koutsoyiannis, D. (2021). 
    Multiscale temporal irreversibility of streamflow and its stochastic modelling. Hydrology, 8(2), 63.
"""

from scipy.stats import skew
from scipy.stats import norm
import numpy as np




def _calculateA( TS ):

    tdTS = TS[ 1: ] - TS[ :-1 ]
    skewness_orig = skew( TS )
    skewness_td = skew( tdTS )
    a = skewness_td / skewness_orig

    return a



def _A_For_Rnd_Series( TS, numRndReps = 100 ):

    a = []
    
    for k in range( numRndReps ):
        tTS = np.random.permutation( np.copy( TS ) )
        a.append( _calculateA( tTS ) )
    
    return a




def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the Skewness test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    numRndReps : int
        Number of random shuffled time series used to estimate the p-value. Optional, default: 100.
    pValueMethod : string
        Method used to estimate the p-value, including 'proportion' and 'z-score'. Optional, default: 'z-score'.

    Returns
    -------
    float
        p-value of the test.
    float
        statistic of the test.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """

    # Setting up the parameters

    numRndReps = kwargs.get( 'numRndReps', 100 )
    pValueMethod = kwargs.get( 'pValueMethod', 'z-score' )


    # Checking the parameters

    if type( numRndReps ) is not int:
        raise ValueError("numRndReps is not an integer")
    if numRndReps < 0:
        raise ValueError("numRndReps must be zero or positive")
    if pValueMethod not in [ 'proportion', 'z-score' ]:
        raise ValueError("pValueMethod not recognised")


    # Computing a for the original time series

    a = _calculateA( TS )

    if numRndReps <= 0:
        return 1.0, a


    # Extract the p-value

    pValue = 1.0
    rndA = _A_For_Rnd_Series( TS, numRndReps )

    if pValueMethod == 'z-score':
        z_score = ( a - np.mean( rndA ) ) / np.std( rndA )
        pValue = norm.sf( z_score )
    if pValueMethod == 'proportion':
        pValue = np.sum( np.abs( a ) < np.abs( np.array( rndA ) ) ) / numRndReps
    
    return pValue, a






def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the Skewness test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.

    Returns
    -------
    float
        statistic of the test.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """

    return GetPValue( TS, numRndReps = 0, **kwargs )[ 1 ]





