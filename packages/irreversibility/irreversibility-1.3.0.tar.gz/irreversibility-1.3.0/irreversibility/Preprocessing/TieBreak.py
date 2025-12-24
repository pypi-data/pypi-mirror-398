
import numpy as np



def Noise( TS, **kwargs ):

    """
    Add a small amplitude noise to break potential ties. The noise is applied to all values, and its amplitude is calculated as the minimum difference between pairs of values, to maintain the ranking.

    Parameters
    ----------
    TS : numpy.array
        Time series to be processed.

    Returns
    -------
    numpy.array
        Processed time series.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """

    deltas = np.sort( TS )
    deltas = deltas[ 1: ] - deltas[ :-1 ]
    minD = np.min( deltas[ deltas > 0 ] )

    TS2 = TS + np.random.uniform( -minD / 2., minD / 2., 
                                  ( np.size( TS ) ) )
    
    return TS2





def NoiseOnTies( TS, **kwargs ):

    """
    Add a small amplitude noise to break potential ties, only on those values that appear in ties. Its amplitude is calculated as the minimum difference between pairs of values.

    Parameters
    ----------
    TS : numpy.array
        Time series to be processed.

    Returns
    -------
    numpy.array
        Processed time series.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """

    deltas = np.sort( TS )
    deltas = deltas[ 1: ] - deltas[ :-1 ]
    minD = np.min( deltas[ deltas > 0 ] )

    TS2 = TS
    for k in range( np.size( TS2 ) ):
        if np.sum( TS2 == TS2[ k ] ) > 1:
            TS2 += np.random.uniform( -minD / 2., minD / 2. )
    
    return TS2
