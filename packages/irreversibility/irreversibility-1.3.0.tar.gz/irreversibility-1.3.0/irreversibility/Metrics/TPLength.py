
"""
Trend Pattern Lengths test

From:
    Morales Herrera, J., & Salgado-García, R. (2024).
    Measuring irreversibility via trend pattern lengths.
    AIP Advances, 14(3).
"""

import numpy as np
from ..optionalNJIT import optional_njit
from scipy.stats import ks_2samp



def _mySign( x ):

    return int( x > 0 )




def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the Trend Pattern Lengths test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.

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


    dTS = TS[ 1: ] - TS[ :-1 ]

    sign = _mySign( TS[ 0 ] )
    segmL_U = []
    segmL_D = []
    start = 0

    for k in range( 1, np.size( dTS ) ):
        if _mySign( dTS[ k ] ) != sign:

            if sign == 0:
                segmL_D.append( k - start )
            else:
                segmL_U.append( k - start )

            sign = _mySign( dTS[ k ] )
            start = k
            continue

    if sign == 0:
        segmL_D.append( np.size( dTS ) - start )
    else:
        segmL_U.append( np.size( dTS ) - start )

    maxL = np.max( segmL_D + segmL_U )
    prob_U = np.zeros( ( maxL ) )
    for k in segmL_U:
        prob_U[ k - 1 ] += 1

    prob_D = np.zeros( ( maxL ) )
    for k in segmL_D:
        prob_D[ k - 1 ] += 1

    totValues = prob_U + prob_D
    prob_U = prob_U[ totValues > 0 ]
    prob_D = prob_D[ totValues > 0 ]

    if np.sum( prob_U ) == 1 or np.sum( prob_D ) == 1:
        return 0.0, 0.0
    
    from scipy.stats import chi2_contingency
    res = chi2_contingency( [ prob_U, prob_D ] )


    from scipy.stats import entropy
    e = entropy( prob_U, prob_D )

    return res[ 1 ], e




def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the Trend Pattern Lengths test.

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


    return GetPValue( TS, **kwargs )[ 1 ]

