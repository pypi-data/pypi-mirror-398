
"""
Diks test

From:
    Diks, C., Van Zwet, W. R., Takens, F., & DeGoede, J. (1996).
    Detecting differences between delay vector distributions. Physical Review E, 53(3), 2169.
"""

import numpy as np
from scipy.special import perm
import scipy.stats as st
from ..optionalNJIT import optional_njit




@optional_njit( cache=True, nogil=True )
def _numba_CreateVectors( TS, embD ):
    
    dimX = int( ( TS.shape[0] - embD ) / embD )
    vectors = np.zeros( ( dimX, embD ) )
    for k in range( 0, dimX ):
        offset = k * embD
        vectors[ k, : ] = TS[ offset : (offset + embD) ]

    return vectors





@optional_njit( cache=True, nogil=True )           
def _numba_funcH( v1, v2, dVar ):
    
    h = v1 - v2
    h = np.linalg.norm( h ) ** 2.0
    h /= 4 * ( dVar ** 2.0 )
    h = np.exp( - h )
    return h




@optional_njit( cache=True, nogil=True )           
def _numba_GetMatrixH_aux( Z, dVar ):
    
    dimZ = Z.shape[ 0 ]
    matrixH = np.zeros( ( dimZ, dimZ ) )
    for k1 in range( dimZ ):
        for k2 in range( dimZ ):
            matrixH[ k1, k2 ] = _numba_funcH( Z[ k1, : ], Z[ k2, : ], dVar )

    return matrixH



def _GetMatrixH( Z, dVar ):
    
    dimZ = Z.shape[ 0 ]
    matrixH = _numba_GetMatrixH_aux( Z, dVar )
    sumH = np.sum( np.ravel( matrixH ) ) / perm( dimZ, 2, exact = True )
    matrixH -= sumH / 2.0

    return matrixH



def _getPhi( i, j, matrixH ):
    
    return matrixH[ i, j ] - _funcG( i, matrixH ) - _funcG( j, matrixH )
    


def _funcG( i, matrixH ):
    
    g = 0.0
    for k in range( np.size( matrixH, 0 ) ):
        if k == i: continue
        g += matrixH[ i, k ]
    g /= perm( np.size( matrixH, 0 ), 2, exact = True ) - 2
    
    return g



def _getQHat( X, Y, dVar ):
    
    sizeX = np.size( X, 0 )
    sizeY = np.size( Y, 0 )
    
    QHat1 = 0.0
    for k1 in range( sizeX ):
        for k2 in range( sizeX ):
            QHat1 += _numba_funcH( X[k1, :], X[k2, :], dVar )
    t = perm( sizeX, 2, exact = True )
    if t == 0: QHat1 = 0.0
    else: QHat1 /= t
    
    QHat2 = 0.0
    for k1 in range( sizeY ):
        for k2 in range( sizeY ):
            QHat2 += _numba_funcH( Y[k1, :], Y[k2, :], dVar )
    t = perm( sizeY, 2, exact = True )
    if t == 0: QHat2 = 0.0
    else: QHat2 /= t
    
    QHat3 = 0.0
    for k1 in range( sizeX ):
        for k2 in range( np.size( Y, 0 ) ):
            QHat3 += _numba_funcH( X[k1, :], Y[k2, :], dVar )
    QHat3 *= 2.0
    t = sizeX * sizeY
    if t == 0: QHat3 = 0.0
    else: QHat3 /= t
    
    QHat = QHat1 + QHat2 - QHat3

    return QHat



def _getVariance( X, Y, dVar ):
    
    Z = np.vstack( ( X, Y ) )
    
    matrixH = _GetMatrixH( Z, dVar )
    
    G = np.zeros( ( np.size( Z, 0 ) ) )
    for k1 in range( np.size( Z, 0 ) ):
        G[ k1 ] = _funcG( k1, matrixH )
    
    variance = 0.0
    for k1 in range( np.size( Z, 0 ) ):
        for k2 in range( np.size( Z, 0 ) ):
            variance += ( matrixH[ k1, k2 ] - G[ k1 ] - G[ k2 ] ) ** 2.0
            
    variance /= perm( np.size( Z, 0 ), 2, exact = True )
    variance *= 2.0 * ( ( np.size( Z, 0 ) - 1 ) ** 2 ) * ( np.size( Z, 0 ) - 2 )
    variance /= np.size( X, 0 ) * ( np.size( X, 0 ) - 1 ) * np.size( Y, 0 ) * ( np.size( Y, 0 ) - 1 ) * ( np.size( Z, 0 ) - 3 )

    return variance




def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the Diks' test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    embD : int
        Embedding dimension. Optional, default: 6.
    dVar : float
        Threshold, relative to the standard deviation of the time series, against which values are defined as positive or negative. Optional, default: 1.5.

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

    TS = np.copy( TS )
    embD = kwargs.get( 'embD', 6 )
    dVar = kwargs.get( 'dVar', 1.5 )


    # Checking the parameters

    if type( embD ) is not int:
        raise ValueError("embD is not an integer")
    if embD <= 0:
        raise ValueError("embD must be larger than 0")
    if type( dVar ) is not float:
        raise ValueError("dVar is not a float")
    if dVar <= 0:
        raise ValueError("dVar must be larger than 0")


    # Calculate test
    
    TS -= np.mean( TS )
    TS /= np.std( TS )

    X = _numba_CreateVectors( TS, embD )
    Y = _numba_CreateVectors( TS[ ::-1 ], embD )

    QHat = _getQHat( X, Y, dVar )
    variance = _getVariance( X, Y, dVar )
    estimatorS = QHat / np.sqrt( variance )  
    pValue = -1
    pValue = st.norm.sf( estimatorS )

    return pValue, QHat




def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the Dik's test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    embD : int
        Embedding dimension. Optional, default: 6.
    dVar : float
        Threshold, relative to the standard deviation of the time series, against which values are defined as positive or negative. Optional, default: 1.5.

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

