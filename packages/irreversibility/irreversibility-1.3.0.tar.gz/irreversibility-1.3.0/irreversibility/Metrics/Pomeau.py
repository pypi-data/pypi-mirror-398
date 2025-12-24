
"""
Pomeau test

From:
    Pomeau, Y. (1982). Symétrie des fluctuations dans le renversement du temps.
    Journal de Physique, 43(6), 859-867.
"""

import numpy as np
from scipy.stats import norm
from ..optionalNJIT import optional_njit




@optional_njit( cache=True, nogil=True )            
def _numba_getPsi( TS, tau = 1 ):
    
    psi = 0.0
    tsLen = TS.shape[0]

    for k in range( tsLen - 3 * tau - 1 ):
    
        psi += TS[ k ] * ( TS[ k + 2 * tau ] - TS[ k + tau ] ) * TS[ k + 3 * tau ]
    
    psi /= float( tsLen - 3 * tau - 1 )
    
    return psi
    



def _shader_getC_Split( TS, tau ):
    from wgpu.utils.compute import compute_with_buffers
    m = np.size( TS )

    A_shape = ( m )

    newTS = TS.astype(np.float32)

    bindings = {
        0: newTS,
        3: np.array(A_shape, dtype=np.uint32),
    }

    shader_src = """
    @group(0) @binding(0)
    var<storage, read> A: array<f32>;
    @group(0) @binding(2)
    var<storage, read_write> C: array<f32>;

    @group(0) @binding(3)
    var<storage, read> A_shape: array<u32>;

    override tau: u32;

    @compute @workgroup_size(1)
    fn main(@builtin(global_invocation_id) gid: vec3<u32>) {

        let m: u32 = A_shape[0];
        var sum: f32 = 0.0;

        var j: u32 = gid.x;
        sum = A[ j ] * ( A[ j + 2 * tau ] - A[ j + tau ] ) * A[ j + 3 * tau ];
        C[ j ] = sum;

        return;
    }
    """


    out = compute_with_buffers(
        input_arrays=bindings,
        output_arrays={2: (m, "f")},
        shader=shader_src,
        constants={'tau': tau},
        n=(m, 1, 1), 
    )

    C = np.frombuffer(out[2], dtype=np.float32)[ :( - 3 * tau - 1 )]
    return np.sum( C )


def _shader_getPsi( TS, tau ):
    C = 0
    if np.size( TS ) < 60000:
        C += _shader_getC_Split( TS, tau = tau )
    else:
        startOffset = 0
        while startOffset + 60000 + 3 * tau + 1 < np.size( TS ):
            C += _shader_getC_Split( TS[ startOffset : startOffset + 60000 + 3 * tau + 1 ], tau = tau )
            startOffset += 60000
        C += _shader_getC_Split( TS[ startOffset : ], tau = tau )

    psi = C / float( np.size( TS ) - 3 * tau - 1 )
    return psi



def GetPValue( TS: np.array, **kwargs ):

    """
    Get p-value according to the Pomeau test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    tau : int
        Lag used in the computation of the function. Optional, default: 1.
    numRndReps : int
        Number of random shuffled time series used to estimate the p-value. Optional, default: 100.
    useShaders : bool
        Whether to use shaders or only CPU computation. Optional, default: False.
    pValueMethod : string
        Method used to estimate the p-value, including 'proportion' and 'z-score'. Optional, default: 'proportional'.

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

    tau = kwargs.get( 'tau', 1 )
    numRndReps = kwargs.get( 'numRndReps', 100 )
    useShaders = kwargs.get( 'useShaders', False )
    pValueMethod = kwargs.get( 'pValueMethod', 'proportion' )


    # Checking the parameters

    if type( tau ) is not int:
        raise ValueError("tau is not an integer")
    if tau <= 0:
        raise ValueError("tau must be larger than 0")
    if type( numRndReps ) is not int:
        raise ValueError("numRndReps is not an integer")
    if numRndReps < 0:
        raise ValueError("numRndReps must be zero or positive")
    if type( useShaders ) is not bool:
        raise ValueError("useShaders is not a bool")
    if pValueMethod not in [ 'proportion', 'z-score' ]:
        raise ValueError("pValueMethod not recognised")


    # Computing the psi for the original time series

    psi = 0.0

    if useShaders:
        psi = _shader_getPsi( TS, tau = tau )
    else:
        psi = _numba_getPsi( TS, tau = tau ) 
    
    if numRndReps <= 0:
        return 1.0, psi
    
    
    # Compute the psi for the shuffled versions of the time series

    rndPsi = []
    for k in range( numRndReps ):
        if useShaders:
            rndPsi.append( _shader_getPsi( np.random.permutation( TS ), tau = tau ) )
        else:
            rndPsi.append( _numba_getPsi( np.random.permutation( TS ), tau = tau ) )
    

    # Extract the p-value

    pValue = 1.0

    if pValueMethod == 'z-score':
        z_score = ( psi - np.mean( rndPsi ) ) / np.std( rndPsi )
        pValue = norm.sf( z_score )
    if pValueMethod == 'proportion':
        pValue = np.sum( np.abs( psi ) < np.abs( np.array( rndPsi ) ) ) / numRndReps
    
    return pValue, psi



def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the Pomeau test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    tau : int
        Lag used in the computation of the function. Optional, default: 1.
    useShaders : bool
        Whether to use shaders or only CPU computation. Optional, default: False.

    Returns
    -------
    float
        statistic of the test.

    Raises
    ------
    ValueError
        If the parameters are not correct.
    """

    return GetPValue( TS, numRndReps = 0, **kwargs )[ 1 ]

