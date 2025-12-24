
"""
Product of powers' test
This test is conceptually similar to the Pomeau's one, as it 
applies a non-linear and asymmetric function on the data.
Note that the original metric, as proposed in the reference below,
has here been modified to simplify the calculation of a statistical
test.

From:
    Nogare, T. D., & Fulcher, B. D. (2025). 
    Identifying statistical indicators of temporal asymmetry using a data-driven approach. 
    arXiv preprint arXiv:2511.15991.
"""

import numpy as np
from scipy.stats import ks_2samp
from ..optionalNJIT import optional_njit



def _compute_C( TS, exponents, abs ):

    tsLen = np.size( TS )
    embDim = np.size( exponents )

    C = []
    for t in range( tsLen - embDim ):
        tVal = np.prod( np.power( TS[ t : ( t + embDim ) ], exponents ) )
        if abs:
            tVal = np.abs( tVal )
        C.append( tVal )

    return np.array( C )




def GetPValue( TS: np.array, **kwargs ):

    """
    Get p-value according to the Product of Powers test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    exponents : numpy.ndarray
        Exponents used to calculate the product of powers. Must be a 1D array of size greater than one. Optional, default: [ 1, 3 ].
    abs : bool
        Indicates whether to calculate the absolute value of each element. Optional, default: True.

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

    exponents = kwargs.get( 'exponents', np.array( [ 1, 3 ] ) )
    abs = kwargs.get( 'abs', True )


    # Checking the parameters

    if type( exponents ) is not np.ndarray:
        raise ValueError("exponents is not a numpy.array")
    if np.size( exponents ) <= 1:
        raise ValueError("The size of exponents must be larger than 1")
    if type( abs ) is not bool:
        raise ValueError("abs is not a bool")



    C_for = _compute_C( TS, exponents = exponents, abs = abs )
    C_rev = _compute_C( TS[ ::-1 ], exponents = exponents, abs = abs )

    res = ks_2samp( C_for, C_rev )
    pValue, stat = res.pvalue, res.statistic
        
    return pValue, stat



def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the Product of Powers test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    exponents : numpy.array
        Exponents used to calculate the product of powers. Must be a 1D array of size greater than one. Optional, default: [ 1, 3 ].
    abs : bool
        Indicates whether to calculate the absolute value of each element. Optional, default: True.

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

