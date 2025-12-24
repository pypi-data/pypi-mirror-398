
"""
BDS test, using the statsmodels implementation.

From:
    Broock, W. A., Scheinkman, J. A., Dechert, W. D., & LeBaron, B. (1996). 
    A test for independence based on the correlation dimension. Econometric reviews, 15(3), 197-235.
"""

import numpy as np
from statsmodels.tsa.stattools import bds



def GetPValue( TS, **kwargs ):


    """
    Get p-value according to the BDS test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    max_dim : int
        The maximum embedding dimension. Optional, default: 2.
    distance : float
        Specifies the distance multiplier to use when computing the test. Optional, default: 1.5.

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

    max_dim = kwargs.get( 'max_dim', 2 )
    distance = kwargs.get( 'distance', 1.5 )


    # Checking the parameters

    if type( max_dim ) is not int:
        raise ValueError("max_dim is not an integer")
    if max_dim <= 0:
        raise ValueError("max_dim must be larger than 0")
    if type( distance ) is not float:
        raise ValueError("distance is not an float")
    if distance <= 0:
        raise ValueError("distance must be larger than 0")


    # Computing the test

    bds_stat, pV = bds( TS, max_dim = max_dim, epsilon = None, distance = distance )

    if pV.size > 1:
        bds_stat = bds_stat[ np.argmin( pV ) ]
        pV = np.min( pV )
    
    return float( pV ), float( bds_stat )



def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the BDS test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    max_dim : int
        The maximum embedding dimension. Optional, default: 2.
    distance : float
        Specifies the distance multiplier to use when computing the test. Optional, default: 1.5.

    Returns
    -------
    float
        statistic of the test.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """

    return GetPValue( TS, **kwargs )[ 1 ]

