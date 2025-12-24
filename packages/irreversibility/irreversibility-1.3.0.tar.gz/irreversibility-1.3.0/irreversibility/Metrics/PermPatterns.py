
"""
Permutation patterns test

From:
    Zanin, M., Rodríguez-González, A., Menasalvas Ruiz, E., & Papo, D. (2018).
    Assessing time series reversibility through permutation patterns. Entropy, 20(9), 665.
"""


try:
    from scipy.stats import binom_test
except:
    from scipy import stats
    binomtest = stats.binomtest
    pass

from itertools import permutations
import numpy as np
from ..optionalNJIT import optional_njit



@optional_njit( cache=True, nogil=True )
def _numba_GetSinglePermutation( TS ):
    
    order = np.argsort( TS )

    return order
    
    
    
@optional_njit( cache=True, nogil=True )
def _numba_GetPermProb( TS, wLength, allPatterns ):
    
    pProb = np.zeros( ( allPatterns.shape[ 0 ] ) )    
    numPatt = allPatterns.shape[ 0 ]
    
    tsLength = TS.shape[0]
    
    for k in range(0, tsLength - wLength ):
        
        subTS = TS[ k : (k + wLength) ]
        pattern = np.argsort( subTS )

        offset = -1        
        for l in range( numPatt ):
            if np.all( allPatterns[l, :] == pattern ):
                offset = l
                break
            
        if offset == -1:
            allPatterns[ numPatt, : ] = pattern
            pProb[ numPatt ] = 1.0
            numPatt += 1
        else:
            pProb[ offset ] += 1.0
            
    allPatterns = allPatterns[ :numPatt, : ]
    pProb = pProb[ :numPatt ]
         
    totPatterns = np.sum( pProb )
    for k in range( numPatt ):
        pProb[k] /= totPatterns
    
    return ( allPatterns, pProb )
    


def _BinomialTestCompatibility( x, p = 0.5 ):

    try:
        if np.sum( x ) == 0: return 0.
        
        pV = binomtest( x[ 0 ], n = np.sum( x ), p = p ).pvalue
    except:
        pV = binom_test( x, p = p )
        pass

    return pV
    

    

def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the Permutation Pattern test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    pSize : int
        Size of the permutation pattern, i.e. embedding dimension. Optional, default: 3.

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

    pSize = kwargs.get( 'pSize', 3 )


    # Checking the parameters

    if type( pSize ) is not int:
        raise ValueError("pSize is not an integer")
    if pSize <= 2:
        raise ValueError("pSize must be larger than two")


    # Compute the test

    res0, res1 = _numba_GetPermProb( np.ravel(TS), pSize, np.array( list( permutations( range( pSize ) ) ) ) )
    
    asym = []
    
    for k in range( len( res0 ) ):
        for l in range( k + 1, len( res0 ) ):
        
            if np.all( res0[ k ] == res0[ l ][::-1] ):
                
                numPatterns = np.size( TS, 0 ) - 3
                x = [ int( res1[ k ] * numPatterns ),  int( res1[ l ] * numPatterns ) ]
                pV = _BinomialTestCompatibility( x )
                asym.append( pV ) 
                break

    asym = np.array( asym )
    
    if np.size( asym ) == 0:
        return 1.0, 0.0
        
    asym = np.min( asym ) * pSize
    if asym > 1.0: asym = 1.0

    return asym, 0.0



    

def GetStatistic( TS, **kwargs ):

    """
    Get the statistics according to the Permutation Pattern test.
    Note: this function is yet to be implemented!

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    pSize : int
        Size of the permutation pattern, i.e. embedding dimension. Optional, default: 3.

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
