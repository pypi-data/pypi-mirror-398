
"""
Local Clustering Coefficient test

From:
    Donges, J. F., Donner, R. V., & Kurths, J. (2013).
    Testing time series irreversibility using complex network methods.
    EPL (Europhysics Letters), 102(1), 10004.
"""

import numpy as np
from scipy.stats import ks_2samp
from ..optionalNJIT import optional_njit


    
        
@optional_njit( cache=True, nogil=True )            
def _numba_GetOneConnectivity( TS, offset ):
    
    tsLength = TS.shape[0]
    subAM = np.zeros( ( tsLength ) )
    if offset < tsLength - 1:
        subAM[ offset + 1 ] = 1

    if offset >= tsLength - 2: return subAM
    if TS[ offset + 1 ] >= TS[ offset ]: return subAM
        
    lastMax = TS[ offset + 1 ]

    for k in range( offset + 2, tsLength ):
        
        if TS[ k ] >= lastMax:
            lastMax = TS[ k ]
            subAM[ k ] = 1

        if lastMax > TS[ offset ]:
            break
            
    return subAM




def _GetFullAM( TS ):

    tsLength = np.size( TS, 0 )
    AM = np.zeros( (tsLength, tsLength) )
    
    for n1 in range( tsLength ):    
        AM[ n1, : ] = _numba_GetOneConnectivity( TS, n1 )
        
    for n1 in range( tsLength ):
        for n2 in range( n1 + 1, tsLength ):
            AM[ n2, n1 ] = AM[ n1, n2 ]
        
    return AM





@optional_njit( cache=True, nogil=True )            
def _numba_GetLocalClusteringCoefficient( AM ):
    
    numNodes = AM.shape[0]
    
    retardedCC = np.zeros( (numNodes) )
    for n1 in range( numNodes ):
        if np.sum( AM[ n1, :n1 ] ) <= 1.0: continue
        for n2 in range( n1 ):
            if AM[ n1, n2 ] == 0: continue
            for n3 in range( n1 ):
                 retardedCC[ n1 ] += AM[ n1, n2 ] * AM[ n2, n3 ] * AM[ n3, n1 ]
    
    advancedCC = np.zeros( (numNodes) )
    for n1 in range( numNodes ):
        if np.sum( AM[ n1, (n1+1): ] ) <= 1.0: continue
        for n2 in range( n1 + 1, numNodes ):
            if AM[ n1, n2 ] == 0: continue
            for n3 in range( n1 + 1, numNodes ):
                 advancedCC[ n1 ] += AM[ n1, n2 ] * AM[ n2, n3 ] * AM[ n3, n1 ]
                
    return retardedCC, advancedCC





    
def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the Local Clustering Coefficient test.

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

    AM = _GetFullAM( TS )
    retardedCC, advancedCC = _numba_GetLocalClusteringCoefficient( AM )
    stat, pV = ks_2samp( retardedCC,  advancedCC )

    return pV, stat



    
def GetStatistic( TS, **kwargs ):

    """
    Get the statistic of the Local Clustering Coefficient test.

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

