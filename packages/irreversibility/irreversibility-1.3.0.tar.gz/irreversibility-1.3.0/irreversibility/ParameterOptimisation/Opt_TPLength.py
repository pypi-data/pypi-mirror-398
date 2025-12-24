
"""
Optimisation of the parameters for the Trend Pattern Lengths test

From:
    Morales Herrera, J., & Salgado-García, R. (2024).
    Measuring irreversibility via trend pattern lengths.
    AIP Advances, 14(3).
"""

import numpy as np
from itertools import product

from irreversibility.Metrics.TPLength import GetPValue


def Optimisation( tsSet, paramSet = None, target = 'p-value', criterion = np.median, numProcesses = -1 ):

    """
    Optimise the parameters for the Trend Pattern Lengths test.
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
