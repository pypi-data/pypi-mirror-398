
"""
Costa index test

From:
    Costa, M.; Goldberger, A.L.; Peng, C.K.
    Broken asymmetry of the human heartbeat: loss of time irreversibility in aging and disease.
    Physical review letters 2005, 95, 198102.
"""

from scipy.stats import norm
import numpy as np




def _Get_A_For_Rnd_Series( TS, tau, numRndReps = 100 ):

    a = []
    
    for k in range( numRndReps ):
        tTS = np.random.permutation( np.copy( TS ) )
        a.append( _Get_A( tTS, tau = tau ) )
    
    return a



def _Get_A_Entropy_For_Rnd_Series( TS, tau, numRndReps = 100 ):

    a = []
    
    for k in range( numRndReps ):
        tTS = np.random.permutation( np.copy( TS ) )
        a.append( _Get_A_Entropy( tTS, tau = tau ) )
    
    return a



def _Get_A( TS, tau ):

    dTS = TS[ tau: ] - TS[ :-tau ]
    a1 = np.sum( dTS > 0 )
    a2 = np.sum( dTS < 0 )
    return np.abs( a1 - a2 ) / ( a1 + a2 )


def _Get_A_Entropy( TS, tau ):

    dTS = TS[ tau: ] - TS[ :-tau ]
    a1 = np.sum( dTS > 0 ) / np.size( TS[ :-tau ] )
    a2 = np.sum( dTS < 0 ) / np.size( TS[ :-tau ] )

    A = a1 * np.log( a1 ) / ( a1 * np.log( a1 ) + a2 * np.log( a2 ) )
    A -= a2 * np.log( a2 ) / ( a1 * np.log( a1 ) + a2 * np.log( a2 ) )
    return np.abs( A )



def GetPValue( TS, numRndReps = 100, **kwargs ):

    """
    Get p-value according to the Costa test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    tau : int
        Lag used in the computation of the function. Optional, default: 1.
    method: string
        Method used in the estimation: 'fraction', 'entropy'. Optional, default: 'fraction'.
    numRndReps : int
        Number of random shuffled time series used to estimate the p-value. Optional, default: 100.
    pValueMethod : string
        Method used to estimate the p-value, including 'proportion' and 'z-score'. Optional, default: 'z-score'.

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

    tau = kwargs.get( 'tau', 1 )
    method = kwargs.get( 'method', 'fraction' )
    numRndReps = kwargs.get( 'numRndReps', 100 )
    pValueMethod = kwargs.get( 'pValueMethod', 'z-score' )


    # Checking the parameters

    if type( tau ) is not int:
        raise ValueError("tau is not an integer")
    if tau <= 0:
        raise ValueError("tau must be larger than 0")
    if method not in [ 'fraction', 'entropy' ]:
        raise ValueError("Method not valid")
    if type( numRndReps ) is not int:
        raise ValueError("numRndReps is not an integer")
    if numRndReps < 0:
        raise ValueError("numRndReps must be zero or positive")
    if pValueMethod not in [ 'proportion', 'z-score' ]:
        raise ValueError("pValueMethod not recognised")


    # Computing the psi for the original time series

    if method == 'fraction':
        a = _Get_A( TS, tau )
    if method == 'entropy':
        a = _Get_A_Entropy( TS, tau )
    
    if numRndReps <= 0:
        return 1.0, a


    # Extract the p-value

    pValue = 1.0
    if method == 'fraction':
        rndA = _Get_A_For_Rnd_Series( TS, tau = tau, numRndReps = numRndReps )
    if method == 'entropy':
        rndA = _Get_A_Entropy_For_Rnd_Series( TS, tau = tau, numRndReps = numRndReps )

    if pValueMethod == 'z-score':
        z_score = ( a - np.mean( rndA ) ) / np.std( rndA )
        pValue = norm.sf( z_score )
    if pValueMethod == 'proportion':
        pValue = np.sum( np.abs( a ) < np.abs( np.array( rndA ) ) ) / numRndReps

    return pValue, a




def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the Costa test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    tau : int
        Lag used in the computation of the function. Optional, default: 1.
    method: string
        Method used in the estimation: 'fraction', 'entropy'. Optional, default: 'fraction'.

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



