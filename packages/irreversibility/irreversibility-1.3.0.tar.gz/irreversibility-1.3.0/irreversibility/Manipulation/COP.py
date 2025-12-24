
"""
Function to manipulate time series using Continuous Ordinal Patterns, 
aimed at increasing (or decreasing) their irreversibility.
For the theory behind this, see:

Zanin, M. (2024).
Manipulating Time Series Irreversibility Through Continuous Ordinal Patterns.
Symmetry, 16(12), 1696.
"""

import numpy as np

from irreversibility.Metrics.COP import _numba_normWindow, _numba_tranfTS

from ..warningHandling import warnUser



def GetTransformedTimeSeries( timeSeries: np.ndarray, test, testParams, \
                              increase: bool = True, pSize: int = 4, \
                              numIterations: int = 1000, \
                              pvThreshold: float = 0.001 ):

    """
    Try to transform the input time series using Continuous Ordinal Patterns, to either increase or decrease its irreversibility. The manipulation is performed by trying to minimise the magnitude of the changes, as measured by a linear correlation.
    
    Parameters
    ----------
    timeSeries : np.ndarray
        Input time series to be manipulated.
    test : function
        Function to be used to calculate the irreversibility. Must be one of the 'GetPValue' functions of this library.
    testParams : dictionary
        Additional parameters to be passed to the irreversibility test function.
    increase : bool
        Defines whether the aim is to increase (true) or decrease (false) the irreversibility
    pSize : int
        Length of the COP used in the transformation.
    numIterations : int
        Number of times a different random transformation is tested.
    pvThreshold : float
        Threshold used to assess if a solution is accepted. When the target is to increase the irreversibility, the p-value of the transformed time series must be below this threshold; the opposite in the case of reducing the irreversibility.

    Returns
    -------
    np.ndarray
        Manipulated time series. If no acceptable solution is found, this corresponds to the original time series.
    float
        Best p-value obtained, i.e. the one of the manipulated time series.
    float
        Linear correlation between the original and manipulated time series.
    """

    if pSize < 2:
        raise ValueError( "pSize cannot be smaller than 2" )
    if pSize == 2:
        warnUser( "Manipulation.COP.GetTransformedTimeSeries", \
                  "While pSize can technically be 2, it is recommended to use larger values." )
    if numIterations < 1:
        raise ValueError( "numIterations cannot be smaller than 1" )

    if increase:
        bestPV = 1.0
    else:
        bestPV = 0.0
        
    bestCorr = 0.0
    bestTS = []

    for k in range( numIterations ):

        x0 = np.random.uniform( 0.0, 1.0, (pSize) )
        patt = _numba_normWindow( x0 )
        w = _numba_tranfTS( timeSeries, patt )

        corrc = np.abs( np.corrcoef( [ timeSeries[ :np.size( w ) ], w ] )[ 0, 1 ] )
        p_value, _ = test( w, **testParams )

        if increase and p_value >= pvThreshold: continue
        if ( not increase ) and p_value < pvThreshold: continue
        if corrc > bestCorr:
            bestPV = p_value
            bestCorr = corrc
            bestTS = w

    if type( bestTS ) == list:
        return bestTS, bestPV, bestCorr
    
    if np.corrcoef( [ timeSeries[ :np.size( bestTS ) ], bestTS ] )[ 0, 1 ] < 0.0:
        bestTS = 1.0 - bestTS

    return bestTS, bestPV, bestCorr

