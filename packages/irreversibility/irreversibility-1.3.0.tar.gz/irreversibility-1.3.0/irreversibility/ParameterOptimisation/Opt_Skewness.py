
"""
Optimisation of the parameters for the Skewness test

From:
    Koutsoyiannis, D. (2019)
    Time's arrow in stochastic characterization and simulation of atmospheric and hydrological processes.
    Hydrol. Sci. J. (64), 1013-1037.
    
    Vavoulogiannis, S., Iliopoulou, T., Dimitriadis, P., & Koutsoyiannis, D. (2021). 
    Multiscale temporal irreversibility of streamflow and its stochastic modelling. Hydrology, 8(2), 63.
"""

import numpy as np
from itertools import product

from irreversibility.Metrics.Skewness import GetPValue


def Optimisation( tsSet, paramSet = None, target = 'p-value', criterion = np.median, numProcesses = -1 ):

    """
    Optimise the parameters for the Skewness test.
    Note that this test has no parameters... hence the function is included for compatibility only.

    Parameters
    ----------
    tsSet : list of numpy.array
        Time series to be used in the optimisation.
    paramSet : list
        None required.
    target : string
        None required.
    criterion : function
        None required.
    numProcesses : int
        None required.
    kwargs : 
        None required.

    Returns
    -------
    dictionary
        Set of best parameters.
    float
        Lowest obtained p-value. If target is 'statistic', best obtained statistic.
    """

    return {}, 1.0
