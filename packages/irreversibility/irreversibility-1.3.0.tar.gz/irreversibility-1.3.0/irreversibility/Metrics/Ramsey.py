
"""
Ramsey test

From:
    Ramsey, J. B., & Rothman, P. (1996).
    Time irreversibility and business cycle asymmetry. Journal of Money, Credit and Banking, 28(1), 1-21.
"""

import numpy as np
from scipy.stats import ttest_ind
from ..optionalNJIT import optional_njit



@optional_njit( cache=True, nogil=True )            
def _numba_auxFunction( TS, kappa ):
    
    numPoints = TS.shape[0]

    mean1 = np.zeros( ( numPoints - 2 * kappa ) )
    mean2 = np.zeros( ( numPoints - 2 * kappa ) )
    for k in range( kappa, numPoints - kappa ):
        mean1[ k - kappa ] = TS[k] * TS[k] * TS[k - kappa]
        mean2[ k - kappa ] = TS[k] * TS[k - kappa] * TS[k - kappa]

    return mean1, mean2    




def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the Ramsey test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    kappa : int
        Lag used in the computation of the function. Optional, default: 1.

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

    kappa = kwargs.get( 'kappa', 1 )


    # Checking the parameters

    if type( kappa ) is not int:
        raise ValueError("kappa is not an integer")
    if kappa <= 0:
        raise ValueError("kappa must be larger than 0")


    # Computing the test

    TS = TS - np.mean( TS )

    mean1, mean2 = _numba_auxFunction( TS, kappa )
    
    _, pV = ttest_ind( mean1, mean2 )
    
    return pV, np.mean( mean2 ) - np.mean( mean1 )



def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the Ramsey test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    kappa : int
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

    return GetPValue( TS, **kwargs )[ 1 ]

