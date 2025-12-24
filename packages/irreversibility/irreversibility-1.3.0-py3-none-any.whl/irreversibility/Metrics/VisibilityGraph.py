
"""
Visibility Graph test

From:
    Lacasa, L., Nunez, A., Roldán, É., Parrondo, J. M., & Luque, B. (2012).
    Time series irreversibility: a visibility graph approach. The European Physical Journal B, 85(6), 1-11.
"""

import numpy as np
from scipy.stats import epps_singleton_2samp, ks_2samp
from scipy.stats import entropy
from ..optionalNJIT import optional_njit




@optional_njit( cache=True, nogil=True )            
def _numba_GetOneDegree( TS, offset, horizon ):
    
    tsLength = TS.shape[0]
    
    tempDegree = 1.0

    if horizon == -1:
        maxDistance = tsLength
    else:
        maxDistance = offset + horizon
        if maxDistance > tsLength:
            maxDistance = tsLength
    
    if TS[ offset + 1 ] >= TS[ offset ]: return tempDegree

    lastMax = TS[ offset + 1 ]

    for k in range( offset + 2, maxDistance ):
        
        if TS[ k ] >= lastMax:
            lastMax = TS[ k ]
            tempDegree += 1

        if lastMax > TS[ offset ]:
            break
            
    return tempDegree
    


def _GetVGDivergence( dD, rD ):
        
    while True:
        if dD[ -1 ] == 0 and rD[ -1 ] == 0:
            dD = dD[ :-1 ]
            rD = rD[ :-1 ]
            continue
        break
    
    dD /= np.sum( dD )
    rD /= np.sum( rD )
    en = entropy( dD + 0.000001, qk = rD + 0.000001 )
    
    return en




@optional_njit( cache=True, nogil=True )            
def _numba_GetAllDegrees( TS, horizon ):

    tsLength = TS.shape[0]
    allDegrees = np.zeros( (tsLength - 2) )
    
    for k in range( tsLength - 2 ):        
        allDegrees[k] = _numba_GetOneDegree( TS, k, horizon )


    degreeDistr = np.zeros( (tsLength) )
    
    for k in range( tsLength ):    
        degreeDistr[ k ] = np.sum( allDegrees == k )

        
    return allDegrees, degreeDistr




@optional_njit( cache=True, nogil=True )            
def _numba_GetAllDegrees_Parallel( TS, horizon ):

    tsLength = TS.shape[0]
    allDegrees = np.zeros( (tsLength - 2) )
    
    for k in range( tsLength - 2 ):        
        allDegrees[k] = _numba_GetOneDegree( TS, k, horizon )


    degreeDistr = np.zeros( (tsLength) )
    
    for k in range( tsLength ):    
        degreeDistr[ k ] = np.sum( allDegrees == k )

        
    return allDegrees, degreeDistr




    
def GetPValue( TS: np.array, **kwargs ):

    """
    Get p-value according to the Visibility Graph test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    horizon : int
        Maximum distance for detecting links. If '-1', the whole time series is analysed. Optional, default: -1.
    parallel : bool
        Activate parallelisation - not yet implemented. Optional, default: False.

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

    horizon = kwargs.get( 'horizon', -1 )
    parallel = kwargs.get( 'parallel', False )


    # Checking the parameters

    if type( horizon ) is not int:
        raise ValueError("horizon is not an integer")
    if horizon < -1:
        raise ValueError("horizon must be larger than 0, or -1")


    # Computing the degree distributions

    if parallel:
        allD, dD = _numba_GetAllDegrees_Parallel( TS, horizon )
        allR, rD = _numba_GetAllDegrees_Parallel( TS[ ::-1 ], horizon )
    else:
        allD, dD = _numba_GetAllDegrees( TS, horizon )
        allR, rD = _numba_GetAllDegrees( TS[ ::-1 ], horizon )


    # Extract the p-value

    pV = 1.0
    try:
        pV = epps_singleton_2samp( allD,  allR )[1]
    except:
        pass

    if pV == 1.0:
        try:
            pV = ks_2samp( allD,  allR )[1]
        except:
            pass
    
    div = _GetVGDivergence( dD, rD )
        
    return pV, div



def GetStatistic( TS, **kwargs ):

    """
    Get the statistic of the Visibility Graph test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    horizon : int
        Maximum distance for detecting links. If '-1', the whole time series is analysed. Optional, default: -1.
    parallel : bool
        Activate parallelisation - not yet implemented. Optional, default: False.

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

