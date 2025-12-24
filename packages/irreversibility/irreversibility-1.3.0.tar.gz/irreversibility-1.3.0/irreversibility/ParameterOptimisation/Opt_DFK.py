
"""
Optimisation of the parameters for the DFK test

From:
    Daw, C. S., Finney, C. E. A., & Kennel, M. B. (2000).
    Symbolic approach for measuring temporal “irreversibility”. Physical Review E, 62(2), 1912.
"""

import numpy as np
from itertools import product
from multiprocessing import Pool
from functools import partial

from irreversibility.Metrics.DFK import GetPValue



def Optimisation( tsSet, paramSet = None, target = 'p-value', criterion = np.median, numProcesses = -1, **kwargs ):

    """
    Optimise the parameters for the BDS test.

    Parameters
    ----------
    tsSet : list of numpy.array
        Time series to be used in the optimisation.
    paramSet : list
        List of parameters' values to be evaluated. For each parameter (in the case of this test, two), the list must contain a list of possible values, e.g. [ [1, 2], [1.0, 1.5] ]. If None, a standard set is used. Optional, default: None.
    target : string
        Target of the optimisation, either 'p-value' or 'statistic'.
    criterion : function
        Function to be applied to the set of p-values to obtain the best option. Optional, default: numpy.median.
    numProcesses : int
        Number of parallel tasks used in the evaluation. If -1, only one task is used. Optional, default: False.
    kwargs : 
        Other options to be passed to the function to obtain the p-values.

    Returns
    -------
    dictionary
        Set of best parameters.
    float
        Lowest obtained p-value. If target is 'statistic', best obtained statistic.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """


    if target not in [ 'p-value', 'statistic' ]:
        raise ValueError( "target should be 'p-value' or 'statistic'" )

    if paramSet is None:
        p1Set = [ 2, 3, 4 ]
        p2Set = [ 2, 3, 4 ]
    else:
        p1Set = paramSet[ 0 ]
        p2Set = paramSet[ 1 ]

    nTarget = 0
    if target == 'statistic':
        nTarget = 1

    if nTarget == 0:
        bestPValue = 1.0
    else:
        bestPValue = -9999.
    bestParameters = []

    for pSet in product( p1Set, p2Set ):

        pV = np.zeros( ( len( tsSet ) ) )

        if numProcesses == -1:

            for k in range( len( tsSet ) ):
                pV[ k ] = GetPValue( tsSet[ k ], n = pSet[ 0 ], L = pSet[ 1 ], **kwargs )[ nTarget ]

        else:

            with Pool( processes = numProcesses ) as pool:

                async_result = []
                for k in range( len( tsSet ) ):
                    func = partial( GetPValue, TS = tsSet[ k ], n = pSet[ 0 ], L = pSet[ 1 ], **kwargs )
                    async_result.append( pool.apply_async( func ) )
                
                [result.wait() for result in async_result]
                for k in range( len( tsSet ) ):
                    pV[ k ] = async_result[ k ].get()[ nTarget ]

        synthPV = criterion( pV )
        if ( synthPV < bestPValue and nTarget == 0 ) or ( synthPV > bestPValue and nTarget == 1 ):
            bestPValue = synthPV
            bestParameters = { 'n': pSet[ 0 ], 'L': pSet[ 1 ] }

    return bestParameters, bestPValue

