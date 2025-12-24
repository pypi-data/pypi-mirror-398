

import numpy as np
from ..optionalNJIT import optional_njit
from ..warningHandling import warnUser


@optional_njit( cache=True, nogil=True )   
def lorenz( tsLen: int = 1000, dT: float = 0.01, x: float = 0.0, \
            y: float = 1.0, z: float = 1.05, \
            s: float = 10, r: float = 28, \
            b: float = 2.667, randomInit: bool = False ) -> np.ndarray :
    
    """
    Generate a time series using the Lorenz system.
    The Lorenz system is defined by the following equations:
    .. math:: \\frac{dx}{dt} = s (y - x)
    .. math:: \\frac{dy}{dt} = r x - y - x z
    .. math:: \\frac{dz}{dt} = x y - b z
    where :math:`x`, :math:`y`, and :math:`z` are the variables of the system,
    and :math:`s`, :math:`r`, and :math:`b` are parameters.

    Parameters
    ----------
    tsLen : int
        Length of the time series to generate.
    dT : float
        Time step for the simulation.
    x : float
        Initial value of the x variable.
    y : float
        Initial value of the y variable.
    z : float
        Initial value of the z variable.
    s : float
        Parameter of the Lorenz system.
    r : float
        Parameter of the Lorenz system.
    b : float
        Parameter of the Lorenz system.
    randomInit : bool
        If True, random initial values are generated for x, y, and z.
    
    Returns
    -------
    np.ndarray
        Generated time series.
    """
      
    if randomInit:
        x = np.random.uniform( -0.5, 0.5 )
        y = np.random.uniform( 0.0, 2.0 )
        z = np.random.uniform( 0.9, 1.1 )

    if s < 0.0:
        warnUser( "TimeSeriesGeneration.Lorenz.lorenz", \
                  "s should be positive" )
    if r < 0.0:
        warnUser( "TimeSeriesGeneration.Lorenz.lorenz", \
                  "r should be positive" )
    if b < 0.0:
        warnUser( "TimeSeriesGeneration.Lorenz.lorenz", \
                  "b should be positive" )
        
    if tsLen < 1:
        raise ValueError( "tsLen must be greater than 0" )
    if dT <= 0.0:
        raise ValueError( "dT must be greater than 0" )
    
    tsLen = int( tsLen )
    TS = np.zeros( (tsLen, 3) )
    TS[0, 0] = x
    TS[0, 1] = y
    TS[0, 2] = z
                                          
    for i in range(1, tsLen):

        x_dot = s * ( TS[i - 1, 1] - TS[i - 1, 0] )
        y_dot = r * TS[i - 1, 0] - TS[i - 1, 1] - TS[i - 1, 0] * TS[i - 1, 2]
        z_dot = TS[i - 1, 0] * TS[i - 1, 1] - b * TS[i - 1, 2]

        TS[i, 0] = TS[i - 1, 0] + (x_dot * dT)
        TS[i, 1] = TS[i - 1, 1] + (y_dot * dT)
        TS[i, 2] = TS[i - 1, 2] + (z_dot * dT)
    
    return TS

