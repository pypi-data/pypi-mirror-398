
"""
Optimisation of the parameters for the Local Clustering Coefficient test

From:
    Donges, J. F., Donner, R. V., & Kurths, J. (2013).
    Testing time series irreversibility using complex network methods.
    EPL (Europhysics Letters), 102(1), 10004.
"""

import numpy as np
from itertools import product

from irreversibility.Metrics.LocalCC import GetPValue


def Optimisation( tsSet, paramSet = None, target = 'p-value', criterion = np.median, numProcesses = -1 ):

    """
    Optimise the parameters for the Local Clustering Coefficient test.
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
