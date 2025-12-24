
"""
Ternary Coding test

From:
    Cammarota, C., & Rogora, E. (2007). 
    Time reversal, symbolic series and irreversibility of human heartbeat. 
    Chaos, Solitons & Fractals, 32(5), 1649-1654.
"""

import numpy as np
from statsmodels.stats.descriptivestats import sign_test
from ..optionalNJIT import optional_njit


    

@optional_njit( cache=True, nogil=True )             
def _numba_auxCountN( TS, alpha ):
    
    Np = 0
    Nn = 0
    
    TS = TS[ 1: ] - TS[ :-1 ]
    
    for k in range( TS.shape[0] - 2 ):
        if TS[ k ] > alpha and TS[ k + 1 ] > alpha and TS[ k + 2 ] > alpha:
            Np += 1
        if TS[ k ] < -alpha and TS[ k + 1 ] < -alpha and TS[ k + 2 ] < -alpha:
            Nn += 1
        
    return Np - Nn




def GetPValue( TS: np.array, **kwargs ):

    """
    Get p-value according to the Ternary Coding test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    segL : int
        Length of the segments. Optional, default: 4.
    alpha : int
        Percentile used to evaluate if a value is extreme. Optional, default: 10.

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

    segL = kwargs.get( 'segL', 4 )
    alpha = kwargs.get( 'alpha', 10 )

    # Checking the parameters

    if type( segL ) is not int:
        raise ValueError("segL is not an integer")
    if segL <= 3:
        raise ValueError("segL must be larger than 3")
    if type( alpha ) is not int:
        raise ValueError("alpha is not an integer")
    if alpha <= 0:
        raise ValueError("alpha must be larger than 0")


    # Compute the test
        
    numSegments = int( np.floor( np.size( TS ) / segL ) )
    if numSegments < 3:
        return 1.0, 0.0
    
    D = TS[ 1: ] - TS[ :-1 ]
    alpha_star = np.percentile( D, alpha )
    
    Nd = []
    for k in range( numSegments ):
        tTS = TS[ ( k * segL ) : ( ( k + 1 ) * segL ) ]
        Nd.append( _numba_auxCountN( tTS, alpha_star ) )
    
    pValue, M = ( 1.0, 0.0 )
    try:
        M, pValue = sign_test( Nd )
    except:
        pass
    
    return pValue, np.abs( M )



def GetStatistic( TS: np.array, **kwargs ):

    """
    Get the statistic according to the Ternary Coding test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    segL : int
        Length of the segments. Optional, default: 4.
    alpha : int
        Percentile used to evaluate if a value is extreme. Optional, default: 10.

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
