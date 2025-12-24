
"""
Utility functions to downsampling a time series.
"""

import numpy as np
from scipy.signal import decimate
from ..warningHandling import warnUser



def __ParametersCheck( tau ):

    if tau < 1:
        raise ValueError( "Tau must be greater than 0" )
    


def OneEveryN( TS: np.ndarray, tau: int ) -> np.ndarray :

    """
    Downsample a time series by keeping one every tau observations.
    
    Parameters
    ----------
    TS : np.ndarray
        Input time series.
    tau : int
        Downsampling factor.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    __ParametersCheck( tau )
    
    return np.copy( TS[ :: tau ] )



def Downsampling_Avg( TS: np.ndarray, tau: int ) -> np.ndarray :

    """
    Downsample a time series by extracting sub-windows of size tau, and substituting their values with the corresponding average.
    
    Parameters
    ----------
    TS : np.ndarray
        Input time series.
    tau : int
        Downsampling factor.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    __ParametersCheck( tau )
    
    newL = int( np.size( TS ) / tau )
    newTS = np.zeros( ( newL ) )
    for k in range( newL ):
        newTS[ k ] = np.mean( TS[ ( k * tau ) : ( (k+1) * tau ) ] )
    return newTS



def Decimate( TS: np.ndarray, tau: int ) -> np.ndarray :

    """
    Downsample a time series through a decimation process; see https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.decimate.html.
    
    Parameters
    ----------
    TS : np.ndarray
        Input time series.
    tau : int
        Downsampling factor.

    Returns
    -------
    np.ndarray
        Generated time series.
    """

    __ParametersCheck( tau )
        
    return decimate( np.copy( TS ), tau )

