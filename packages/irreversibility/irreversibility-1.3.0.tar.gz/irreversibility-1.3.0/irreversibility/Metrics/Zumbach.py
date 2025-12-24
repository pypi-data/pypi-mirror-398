
"""
Zumbach test

From:
    Zumbach, G. (2009).
    Time reversal invariance in finance.
    Quantitative Finance, 9(5), 505-515.
"""

import numpy as np
from scipy.stats import skew
from scipy.stats import norm




def _calcAllReturns( ts, granularity ):

    ts = np.log2( ts )
    return ts[ granularity : ] - ts[ : (-granularity) ]



def _histVolatility( ts, t, deltaT, allRets ):

    ax = []
    for k in range( t - deltaT, t ):
        if k < 0: continue
        if k >= np.size( allRets ): continue
        ax.append( allRets[ k ] ** 2.0 )
    
    return np.mean( ax )



def _realVolatility( ts, t, deltaT, allRets, granularity ):

    ax = []
    for k in range( t + granularity, t + deltaT ):
        if k >= np.size( allRets ): continue
        ax.append( allRets[ k ] ** 2.0 )
    
    return np.mean( ax )





def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the Zumbach test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    deltaT : int
        Size of the window used to calculate the volatility. Optional, default: 20.
    granularity : int
        Number of values skipped to calculate the real volatility. Optional, default: 3.

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

    deltaT = kwargs.get( 'deltaT', 20 )
    granularity = kwargs.get( 'granularity', 3 )


    # Checking the parameters

    if type( deltaT ) is not int:
        raise ValueError("deltaT is not an integer")
    if deltaT <= 1:
        raise ValueError("deltaT must be larger than one")
    if type( granularity ) is not int:
        raise ValueError("granularity is not an integer")
    if granularity <= 1:
        raise ValueError("granularity must be larger than one")


    # Calculate the test

    allRets = _calcAllReturns( TS, granularity )

    set1 = []
    set2 = []
    for t in range( np.size( TS ) ):
        set1.append( _histVolatility( TS, t, deltaT, allRets ) )
        set2.append( _realVolatility( TS, t, deltaT, allRets, granularity ) )

    set1 = np.array( set1 )
    set2 = np.array( set2 )
    notValid = np.any( ( np.isnan( set1 ), np.isnan( set2 ) ), axis = 0 )

    set1 = set1[ ~notValid ]
    set2 = set2[ ~notValid ]

    from scipy.stats import ks_2samp
    if np.size( set1 ) == 0 or np.size( set2 ) == 0:
        return 1.0, 0.0
    
    stat, pV = ks_2samp( set1,  set2 )

    return pV, stat



def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the Zumbach test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    deltaT : int
        Size of the window used to calculate the volatility. Optional, default: 20.
    granularity : int
        Number of values skipped to calculate the real volatility. Optional, default: 3.

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

