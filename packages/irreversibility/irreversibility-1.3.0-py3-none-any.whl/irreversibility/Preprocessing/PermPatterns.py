

import numpy as np
from itertools import permutations
from scipy.stats import norm
from ..optionalNJIT import optional_njit



def TimeSeriesToPermPatterns( TS, pSize: int = 3, overlapping: bool = True ):

    """
    Convert a time series into a sequence of permutation patterns.

    Parameters
    ----------
    TS : numpy.array
        Time series to be processed.
    pSize : int
        Embedding dimension, or number of points used to reconstruct each permutation pattern. Optional, default: 3.
    overlapping: bool
        Indicate whether the permutation patterns are calculated over overlapping or not segments of the original time series. Optional, default: True.

    Returns
    -------
    numpy.array
        Processed time series.
    numpy.array
        A list of the permutation patterns used in the conversion.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """

    if type( pSize ) is not int:
        raise ValueError("pSize is not an integer")
    if pSize < 2:
        raise ValueError("pSize cannot be smaller than 2")

    allPatts = np.array( list( permutations( range( pSize ) ) ) )

    encodedTS = []
    tStep = pSize
    if overlapping: tStep = 1

    for offset in range( 0, np.size( TS ) - pSize, tStep ):

        subTS = TS[ offset : ( offset + pSize ) ]
        order = np.argsort( subTS )
        delta = np.sum( np.abs( allPatts - order ), axis = 1 )
        index = np.argmin( delta )
        encodedTS.append( index )

    encodedTS = np.array( encodedTS )

    return encodedTS, allPatts

