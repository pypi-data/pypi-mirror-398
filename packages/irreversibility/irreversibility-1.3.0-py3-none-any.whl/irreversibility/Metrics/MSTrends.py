
"""
Micro-scale trends test

From:
    Zanin, M. (2021). Assessing time series irreversibility through micro-scale trends. 
    Chaos: An Interdisciplinary Journal of Nonlinear Science, 31(10).
"""

import numpy as np
from scipy import stats
from scipy.stats import skew
from ..optionalNJIT import optional_njit




@optional_njit( cache=True, nogil=True )
def _numba_OneSlope( Y, wSize ):

    X = np.arange( wSize )
    xMean = np.mean( X )
    yMean = np.mean( Y )
    X = X - xMean
    Y = Y - yMean

    res = 0.0
    for k in range( wSize ):
        res += X[k] * Y[k]

    res2 = 0.0
    for k in range( wSize ):
        res2 += X[k] * X[k]

    return res / res2



@optional_njit( cache=True, nogil=True )
def _numba_SlopeIrreversibility_aux( TS, wSize ):

    numSamples = TS.shape[0]
    allSlopes = np.zeros((numSamples - wSize))

    for k in range(numSamples - wSize):
        subTS = TS[k: k + wSize]
        allSlopes[k] = _numba_OneSlope( subTS, wSize )

    return allSlopes





@optional_njit( cache=True, nogil=True )
def _numba_SlopeIrreversibility_aux_2( TS, wSize2 ):

    tsLen = TS.shape[0]
    TSStd = np.zeros ( (tsLen - 2 * wSize2) )
    for k in range ( wSize2, tsLen - wSize2 ):
        TSStd[ k - wSize2 ] = np.std ( TS[ k - wSize2 : k + wSize2 ] )

    return TSStd





@optional_njit( cache=True, nogil=True )
def _numba_SlopeIrreversibility_aux_3( TS, wSize2 ):

    tsLen = TS.shape[0]
    TSStd = np.zeros ( (tsLen - 2 * wSize2) )
    for k in range ( wSize2, tsLen - wSize2 ):

        temp = ( TS[ k - wSize2 : k + wSize2 ] - np.mean( TS[ k - wSize2 : k + wSize2 ] ) )
        temp = np.power( temp, 3.0 )
        temp2 = np.sum( temp )
        temp2 = temp2 / float( tsLen - 2 * wSize2 )

        tempv = np.std( TS[ k - wSize2 : k + wSize2 ] )
        tempv = np.power( tempv, 3.0 )
        temp3 = temp2 / tempv
        TSStd[ k - wSize2 ] = temp3

    return TSStd




@optional_njit( cache=True, nogil=True )
def _numba_SlopeIrreversibility_aux_3b( TS, wSize2 ):

    tsLen = TS.shape[0]
    TSStd = np.zeros ( (tsLen - 2 * wSize2) )
    for k in range ( wSize2, tsLen - wSize2 ):
        TSStd[ k - wSize2 ] = skew( TS[ k - wSize2 : k + wSize2 ] )

    return TSStd





def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the MSTrends test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    wSize : int
        Size of the small window. Optional, default: 2.
    wSize2 : int
        Size of the large window. Optional, default: 20.

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

    wSize = kwargs.get( 'wSize', 2 )
    wSize2 = kwargs.get( 'wSize2', 20 )


    # Checking the parameters

    if type( wSize ) is not int:
        raise ValueError("wSize is not an integer")
    if wSize <= 0:
        raise ValueError("wSize must be larger than 0")
    if type( wSize2 ) is not int:
        raise ValueError("wSize2 is not an integer")
    if wSize2 <= 0:
        raise ValueError("wSize2 must be larger than 0")


    # Calculate the test

    allSlopes = _numba_SlopeIrreversibility_aux( TS, wSize )
    res1 = stats.ks_2samp(allSlopes, -allSlopes)

    res2 = [ 0.0, 1.0 ]
    try:
        TSStd = _numba_SlopeIrreversibility_aux_2( TS, wSize2 )
        allSlopes2 = _numba_SlopeIrreversibility_aux( TSStd, wSize )
        res2 = stats.ks_2samp(allSlopes2, -allSlopes2)
    except:
        pass

    res3 = [ 0.0, 1.0 ]
    try:
        TSSkew = _numba_SlopeIrreversibility_aux_3( TS, wSize2 )
        allSlopes3 = _numba_SlopeIrreversibility_aux( TSSkew, wSize )
        res3 = stats.ks_2samp(allSlopes3, -allSlopes3)
    except:
        pass

    p_value = np.min( [ res1[1], res2[1], res3[1] ] ) * 3.0
    stat = np.max( [ res1[0], res2[0], res3[0] ] )

    if p_value > 1.0: p_value = 1.0

    return p_value, stat






def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the MSTrends test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    wSize : int
        Size of the small window. Optional, default: 2.
    wSize2 : int
        Size of the large window. Optional, default: 20.

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

    