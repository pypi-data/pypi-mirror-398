
"""
Detailed Balance test

From:
    Under consideration
"""


import numpy as np
from scipy.stats import entropy
from scipy.stats import norm
from ..optionalNJIT import optional_njit




def ScramblePaths( Paths ):

    """
    Scramble the paths in the list of paths.
    """

    newPaths = []
    for i in range( len( Paths ) ):
        newPaths.append( np.random.permutation( Paths[ i ] ) )

    return newPaths



@optional_njit( cache=True, nogil=True )
def __GetOneJSD( Paths, numNodes, node ):

    pOut = np.zeros( ( numNodes ) )
    for path in Paths:

        for t in range( len( path ) - 1 ):
            if path[ t ] == node:
                pOut[ path[ t + 1 ] ] += 1
    nWalks = np.sum( pOut )
    if np.sum( pOut ) > 0:
        pOut = pOut / np.sum( pOut )

    pIn = np.zeros( ( numNodes ) )
    for path in Paths:

        for t in range( 1, len( path ) ):
            if path[ t ] == node:
                pIn[ path[ t - 1 ] ] += 1
    nWalks = ( nWalks + np.sum( pIn ) )
    if np.sum( pIn ) > 0:
        pIn = pIn / np.sum( pIn )

    return pIn, pOut, nWalks



@optional_njit( cache=True, nogil=True )
def __GetOneJSD_Conditional( Paths, numNodes, node, nodeC ):

    pOut = np.zeros( ( numNodes ) )
    for path in Paths:

        for t in range( 1, len( path ) - 1 ):
            if path[ t ] == node and path[ t-1 ] == nodeC:
                pOut[ path[ t + 1 ] ] += 1
    nWalks = np.sum( pOut )
    if np.sum( pOut ) > 0:
        pOut = pOut / np.sum( pOut )

    pIn = np.zeros( ( numNodes ) )
    for path in Paths:

        for t in range( 1, len( path ) - 1 ):
            if path[ t ] == node and path[ t+1 ] == nodeC:
                pIn[ path[ t - 1 ] ] += 1

    nWalks = ( nWalks + np.sum( pIn ) )
    if np.sum( pIn ) > 0:
        pIn = pIn / np.sum( pIn )

    return pIn, pOut, nWalks



def GetTotalJSD( Paths ):

    TotalJSD = 0.

    numNodes = 0
    for path in Paths:
        numNodes = max( numNodes, np.max( path ) )
    numNodes += 1

    for node in range( numNodes ):

        pIn, pOut, nWalks = __GetOneJSD( Paths, numNodes, node )

        pMix = pIn + pOut
        if np.sum( pMix ) == 0:
            continue
        pMix = pMix / np.sum( pMix )
        
        JSD = 0.5 * entropy( pIn, pMix ) + \
            0.5 * entropy( pOut, pMix )
        if np.isnan( JSD ):
            JSD = 0.

        TotalJSD += JSD * nWalks

    return TotalJSD



def GetTotalJSD_Conditional( Paths ):

    TotalJSD = 0.

    numNodes = 0
    for path in Paths:
        numNodes = max( numNodes, np.max( path ) )
    numNodes += 1

    for node in range( numNodes ):
        for nodeC in range( numNodes ):

            pIn, pOut, nWalks = __GetOneJSD_Conditional( \
                Paths, numNodes, node, nodeC )

            pMix = pIn + pOut
            if np.sum( pMix ) == 0:
                continue
            pMix = pMix / np.sum( pMix )
            
            JSD = 0.5 * entropy( pIn, pMix ) + \
                0.5 * entropy( pOut, pMix )
            if np.isnan( JSD ):
                JSD = 0.

            TotalJSD += JSD * nWalks

    return TotalJSD



def GetPValue( Walks, conditional = False, numRndReps = 100, **kwargs ):

    """
    Get p-value according to the Detailed Balance test.

    Parameters
    ----------
    TS : numpy.array or list
        Time series to be analysed. This can be a list of numpy arrays in a list.
    conditional : bool
        Define whether to calculate conditional probabilities between symbols, using past values
    numRndReps : int
        Number of random shuffled time series used to estimate the p-value. Optional, default: 100.

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

    p_value, J, _ = GetPValue_and_ZScore( Walks, conditional = conditional, numRndReps = numRndReps, **kwargs )

    return p_value, J



def GetPValue_and_ZScore( Walks, numRndReps = 100, conditional = False, **kwargs ):

    """
    Get p-value ND Z-Score according to the Detailed Balance test.

    Parameters
    ----------
    TS : numpy.array or list
        Time series to be analysed. This can be a list of numpy arrays in a list.
    conditional : bool
        Define whether to calculate conditional probabilities between symbols, using past values
    numRndReps : int
        Number of random shuffled time series used to estimate the p-value. Optional, default: 100.

    Returns
    -------
    float
        p-value of the test.
    float
        statistic of the test.
    float
        ZScore of the test.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """
    
    NPWalks = []
    if type( Walks ) == np.ndarray:
        NPWalks.append( Walks )
    else:
        for path in Walks:
            NPWalks.append( np.array( path ) )

    if conditional:
        J = GetTotalJSD_Conditional( NPWalks )
    else:
        J = GetTotalJSD( NPWalks )

    z_score = 0.
    p_value = 1.

    if numRndReps > 0:
        rndJ = []
        for k in range( numRndReps ):
            rndWalks = ScramblePaths( NPWalks )
            if conditional:
                rndJ.append( GetTotalJSD_Conditional( rndWalks ) )
            else:
                rndJ.append( GetTotalJSD( rndWalks ) )

        z_score = ( np.abs( J ) - np.mean( np.abs( rndJ ) ) ) / np.std( rndJ )
        p_value = norm.sf( z_score )

    return p_value, J, z_score




def GetStatistic( TS, conditional = False, **kwargs ):

    """
    Get the statistic according to the Costa test.

    Parameters
    ----------
    TS : numpy.array or list
        Time series to be analysed. This can be a list of numpy arrays in a list.
    conditional : bool
        Define whether to calculate conditional probabilities between symbols, using past values

    Returns
    -------
    float
        statistic of the test.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """
    
    return GetPValue( TS, conditional = conditional, numRndReps = -1, **kwargs )[ 1 ]

