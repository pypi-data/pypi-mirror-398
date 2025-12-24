
"""
DFK test

From:
    Daw, C. S., Finney, C. E. A., & Kennel, M. B. (2000).
    Symbolic approach for measuring temporal “irreversibility”. Physical Review E, 62(2), 1912.
"""

import numpy as np
from scipy.stats import chisquare
from ..optionalNJIT import optional_njit


    
    
def _GetSymbolicTimeSeries( TS, n ):
    
    numPoints = TS.shape[0]
    sortedTS = np.argsort( TS )
    thresholds_arg = np.array( [ sortedTS[ int( (k+1) * numPoints / n ) ] for k in range( n-1 ) ] )
    thresholds = TS[ thresholds_arg ]
    
    symbTS = np.zeros( ( numPoints ) )
    for offset in range( numPoints ):
        
        if TS[ offset ] < thresholds[0]:
            continue
        
        if TS[ offset ] >= thresholds[-1]:
            symbTS[ offset ] = n - 1
            
        for k in range( 0, n-2 ):
            if TS[ offset ] >= thresholds[ k ] and TS[ offset ] < thresholds[ k+1 ]:
                symbTS[ offset ] = k + 1
                break

    return symbTS



@optional_njit( cache=True, nogil=True )            
def _numba_GetWordsTimeSeries( symbTS, n, L ):
   
    numPoints = symbTS.shape[0]
    wordsTS = np.zeros( ( numPoints - L ) )
    for offset in range( numPoints - L ):
        
        currentW = 0
        for l in range( L ):
            currentW += symbTS[ offset + l ] * np.power( n, l )
        wordsTS[ offset ] = currentW
        
    return wordsTS





def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the DFK test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    n : int
        Number of symbols to be used. Optional, default: 3.
    L : int
        Number of symbols merged to create each word. Optional, default: 3.

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

    n = kwargs.get( 'n', 3 )
    L = kwargs.get( 'L', 3 )


    # Checking the parameters

    if type( n ) is not int:
        raise ValueError("n is not an integer")
    if n <= 1:
        raise ValueError("n must be larger than 1")
    if type( L ) is not int:
        raise ValueError("L is not an integer")
    if L <= 1:
        raise ValueError("L must be larger than 1")


    # Computing the test

    numWords = int( np.power( n, L ) )
    
    if np.size( TS ) <= numWords * 2:
        return 1.0, 0.0
    
    symbTS = _GetSymbolicTimeSeries( TS, n )
    wordsTS = _numba_GetWordsTimeSeries( symbTS, n, L )
    freqWords = np.array( [ np.sum( wordsTS == word ) for word in range( numWords ) ], dtype = float )
    
    symbTS_r = _GetSymbolicTimeSeries( TS[::-1], n )
    wordsTS_r = _numba_GetWordsTimeSeries( symbTS_r, n, L )
    freqWords_r = np.array( [ np.sum( wordsTS_r == word ) for word in range( numWords ) ], dtype = float )
    
    if np.sum( freqWords < 0.5 ) + np.sum( freqWords_r < 0.5 ) > 0:
        freqWords += 0.001
        freqWords_r += 0.001
    
    chisq, pV = chisquare( freqWords, freqWords_r )
    
    if pV == 0.0:
        return 1.0, 0.0
    
    return pV, chisq



def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the DFK test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    n : int
        Number of symbols to be used. Optional, default: 3.
    L : int
        Number of symbols merged to create each word. Optional, default: 3.

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