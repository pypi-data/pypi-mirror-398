
"""
Casali test.

From:
    Casali, K. R., Casali, A. G., Montano, N., Irigoyen, M. C., Macagnan, F., Guzzetti, S., & Porta, A. (2008).
    Multiple testing strategy for the detection of temporal irreversibility in stationary time series.
    Physical Review E—Statistical, Nonlinear, and Soft Matter Physics, 77(6), 066204.
"""

import numpy as np
from scipy.stats import norm
from ..optionalNJIT import optional_njit




@optional_njit( cache=True, nogil=True )            
def _numba_CalculateS( TS, m ):

    k = 2. ** (- 0.5 )
    N = TS.shape[ 0 ]

    S_m = 0.
    denom = 0.
    for i in range( 1, N - m ):
        d_mi = k * ( TS[ i ] - TS[ i + m ] )
        S_m += d_mi ** 3.
        denom += d_mi ** 2.

    S_m /= denom ** ( 3. / 2. )

    return S_m



def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the Casali test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    m : int
        Lag used in the computation of the function. Optional, default: 1.
    numRndReps : int
        Number of random shuffled time series used to estimate the p-value. Optional, default: 100.
    pValueMethod : string
        Method used to estimate the p-value, including 'proportion' and 'z-score'. Optional, default: 'proportional'.

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

    m = kwargs.get( 'm', 1 )
    numRndReps = kwargs.get( 'numRndReps', 100 )
    pValueMethod = kwargs.get( 'pValueMethod', 'proportion' )


    # Checking the parameters

    if type( m ) is not int:
        raise ValueError("m is not an integer")
    if m <= 0:
        raise ValueError("m must be larger than 0")
    if type( numRndReps ) is not int:
        raise ValueError("numRndReps is not an integer")
    if numRndReps < 0:
        raise ValueError("numRndReps must be zero or positive")
    if pValueMethod not in [ 'proportion', 'z-score' ]:
        raise ValueError("pValueMethod not recognised")


    # Computing the statistics for the original time series

    S = _numba_CalculateS( TS, m = m )
    
    if numRndReps <= 0:
        return 1.0, S
    
    
    # Compute the statistics for the shuffled versions of the time series

    rndS = []
    for k in range( numRndReps ):
        rndS.append( _numba_CalculateS( np.random.permutation( TS ), m = m ) )


    # Extract the p-value

    pValue = 1.0

    if pValueMethod == 'z-score':
        z_score = ( S - np.mean( rndS ) ) / np.std( rndS )
        pValue = norm.sf( z_score )
    if pValueMethod == 'proportion':
        pValue = np.sum( np.abs( S ) < np.abs( np.array( rndS ) ) ) / numRndReps
    
    return pValue, S




def GetStatistic( TS, **kwargs ):

    """
    Get the statistics according to the Casali test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    m : int
        Lag used in the computation of the function. Optional, default: 1.

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


