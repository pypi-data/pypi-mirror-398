
import numpy as np
from ..optionalNJIT import optional_njit
from ..warningHandling import warnUser


@optional_njit( cache=True, nogil=True )            
def OrnsteinUhlenbeck( tsLen: int = 1000, x: float = 0.0, \
                       Omega: float = 0.1, avg: float = 0.0, \
                       delta: float = 1.0, \
                       randomInit: bool = False ) -> np.ndarray :
      
    """
    Generate a time series using the Ornstein-Uhlenbeck process.
    The Ornstein-Uhlenbeck process is defined as:
    .. math:: dx_t = \\theta (\\mu - x_t) dt + \\sigma dW_t
    where :math:`x_t` is the value at time step :math:`t`, :math:`\\theta` is the rate of mean reversion,
    :math:`\\mu` is the long-term mean, :math:`\\sigma` is the volatility, and :math:`dW_t` is a Wiener process.
    
    Parameters
    ----------
    tsLen : int
        Length of the time series to generate.
    x : float
        Initial value of the time series.
    Omega : float
        Rate of mean reversion.
    avg : float
        Long-term mean.
    delta : float
        Volatility.
    randomInit : bool
        If True, a random initial value is generated between 0.0 and 1.0.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    if randomInit:
        x = np.random.uniform( 0.0, 1.0 )

    if tsLen < 1:
        raise ValueError( "tsLen must be greater than 0" )
    if delta < 0.0:
        raise ValueError( "delta must be greater than 0" )

    TS = np.zeros( (tsLen) )
    TS[0] = x
                                          
    for i in range(1, tsLen):

        x_dot = np.random.normal( 0.0, delta )   
        x_dot = Omega * ( avg - TS[i - 1] ) + x_dot
        TS[i] += x_dot
    
    return TS

