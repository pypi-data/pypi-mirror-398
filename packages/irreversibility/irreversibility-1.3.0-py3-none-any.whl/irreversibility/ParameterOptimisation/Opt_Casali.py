
"""
Optimisation of the parameters for the Casali test.

From:
    Casali, K. R., Casali, A. G., Montano, N., Irigoyen, M. C., Macagnan, F., Guzzetti, S., & Porta, A. (2008).
    Multiple testing strategy for the detection of temporal irreversibility in stationary time series.
    Physical Review E—Statistical, Nonlinear, and Soft Matter Physics, 77(6), 066204.
"""

import numpy as np
from itertools import product
from multiprocessing import Pool
from functools import partial

from irreversibility.Metrics.Casali import GetPValue



def Optimisation( tsSet, paramSet = None, target = 'p-value', criterion = np.median, numProcesses = -1, **kwargs ):

    """
    Optimise the parameters for the Casali test.

    Parameters
    ----------
    tsSet : list of numpy.array
        Time series to be used in the optimisation.
    paramSet : list
        List of parameters' values to be evaluated. For each parameter (in the case of this test, one), the list must contain a list of possible values, e.g. [ [1, 2] ]. If None, a standard set is used. Optional, default: None.
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
        p1Set = np.arange( 1, 101, dtype = int )
    else:
        p1Set = paramSet[ 0 ]

    nTarget = 0
    if target == 'statistic':
        nTarget = 1

    if nTarget == 0:
        bestPValue = 1.0
    else:
        bestPValue = -9999.
    bestParameters = []

    for pSet in p1Set:

        pV = np.zeros( ( len( tsSet ) ) )

        if numProcesses == -1:

            for k in range( len( tsSet ) ):
                pV[ k ] = GetPValue( tsSet[ k ], m = int( pSet ), **kwargs )[ nTarget ]

        else:

            with Pool( processes = numProcesses ) as pool:

                async_result = []
                for k in range( len( tsSet ) ):
                    func = partial( GetPValue, TS = tsSet[ k ], m = int( pSet ), **kwargs )
                    async_result.append( pool.apply_async( func ) )
                
                [result.wait() for result in async_result]
                for k in range( len( tsSet ) ):
                    pV[ k ] = async_result[ k ].get()[ nTarget ]

        synthPV = criterion( pV )
        if ( synthPV < bestPValue and nTarget == 0 ) or ( synthPV > bestPValue and nTarget == 1 ):
            bestPValue = synthPV
            bestParameters = { 'm': pSet }

    return bestParameters, bestPValue


