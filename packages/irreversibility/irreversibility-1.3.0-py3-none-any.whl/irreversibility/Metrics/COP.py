
"""
Continuous Ordinal Patterns test

From:
    Zanin, M. (2023).
    Continuous ordinal patterns: Creating a bridge between ordinal analysis and deep learning.
    Chaos: An Interdisciplinary Journal of Nonlinear Science 33 (3).
"""

import numpy as np
from ..optionalNJIT import optional_njit
from scipy.stats import ks_2samp



@optional_njit( cache=True, nogil=True )
def _numba_normWindow( ts ):
	
	newTS = np.copy( ts )
	newTS -= np.min( newTS )
	newTS /= np.max( newTS )
	newTS = ( newTS - 0.5 ) * 2.0
	return newTS
	
		


@optional_njit( cache=True, nogil=True )            
def _numba_tranfTS( ts, patt ):
	
    tsL = ts.shape[0]
    W = np.zeros( ( tsL - patt.shape[0] + 1 ) )
	
    for t in range( tsL - patt.shape[0] + 1 ):
		
        for l in range( patt.shape[0] ):
            
            W[ t ] += np.abs( _numba_normWindow( ts[ t : ( t + patt.shape[0] ) ] )[ l ] - patt[ l ] )

        W[ t ] = W[ t ] / patt.shape[0] / 2.0
		
    return W



def _shader_tranfTS_Split( ts, patt ):

    from wgpu.utils.compute import compute_with_buffers
    m = np.size( ts )
    n = np.size( patt )

    A_shape = ( m )
    B_shape = ( n )

    bindings = {
        0: ts.astype(np.float32),
        1: patt.astype( np.float32 ),
        3: np.array(A_shape, dtype=np.uint32),
        4: np.array(B_shape, dtype=np.uint32),
    }

    shader_src = """
    @group(0) @binding(0)
    var<storage, read> A: array<f32>;
    @group(0) @binding(1)
    var<storage, read> B: array<f32>;
    @group(0) @binding(2)
    var<storage, read_write> C: array<f32>;

    @group(0) @binding(3)
    var<storage, read> A_shape: array<u32>;

    override n: u32;

    @compute @workgroup_size(1)
    fn main(@builtin(global_invocation_id) gid: vec3<u32>) {

        let m: u32 = A_shape[0];
        var distance: f32 = 0.;

        var j: u32 = gid.x;

        var minV: f32 = 999999.9;
        for (var i: u32 = 0; i < n; i++) {
            if A[ j + i ] < minV {
                minV = A[ j + i ];
            }
        }        

        var subW: array<f32, 100>;
        for (var i: u32 = 0; i < n; i++) {
            subW[ i ] = A[ j + i ] - minV;
        }

        var maxV: f32 = -999999.9;
        for (var i: u32 = 0; i < n; i++) {
            if subW[ i ] > maxV {
                maxV = subW[ i ];
            }
        }        

        for (var i: u32 = 0; i < n; i++) {
            subW[ i ] = subW[ i ] / maxV;
            subW[ i ] = ( subW[ i ] - 0.5 ) * 2.;
        }
        
        for (var i: u32 = 0; i < n; i++) {
            distance += abs( subW[ i ] - B[ i ] );
        }
        
        C[ j ] = distance;

        return;
    }
    """

    out = compute_with_buffers(
        input_arrays=bindings,
        output_arrays={2: (m, "f")},
        shader=shader_src,
        constants={'n': n},
        n=(m, 1, 1), 
    )

    C = np.frombuffer(out[2], dtype=np.float32) / n / 2.
    return C



def _shader_tranfTS( TS, patt ):
    C = np.zeros( (0) )
    if np.size( TS ) < 60000:
        C = _shader_tranfTS_Split( TS, patt )[ : - patt.shape[0] + 1 ]
    else:
        startOffset = 0
        while startOffset + 60000 + patt.shape[0] - 1 < np.size( TS ):
            ax = _shader_tranfTS_Split( \
                TS[ startOffset : startOffset + 60000 + patt.shape[0] - 1 ], \
                patt )[ : - patt.shape[0] + 1 ]
            C = np.hstack( ( C, ax ) )
            startOffset += 60000
        ax = _shader_tranfTS_Split( TS[ startOffset : ], patt )[ : - patt.shape[0] + 1 ]
        C = np.hstack( ( C, ax ) )

    return C





def _evaluateDistance( patt, TS1, TS2, useShaders ):
    
    patt = _numba_normWindow( patt )
    
    d_0 = np.empty( ( 0, 1 ) )
    d_r = np.empty( ( 0, 1 ) )

    TS = TS1
    if useShaders:
        w = _shader_tranfTS( TS, patt )
    else:
        w = _numba_tranfTS( TS, patt )
    w[ np.isnan( w ) ] = 0.0
    d_0 = w
    
    TS = TS2
    if useShaders:
        w = _shader_tranfTS( TS, patt )
    else:
        w = _numba_tranfTS( TS, patt )
    w[ np.isnan( w ) ] = 0.0
    d_r = w

    allRes = ks_2samp( d_0, d_r )
       
    return allRes[ 1 ], allRes[ 0 ]



def GetPValue( TS, **kwargs ):

    """
    Get p-value according to the Continuous Ordinal Pattern test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    pSize : int
        Size of the pattern. Optional, default: 3.
    numIters : int
        Number of random patterns to be tested. Optional, default: function of the pattern size.
    useShaders : bool
        Whether to use shaders or only CPU computation. Optional, default: False.

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

    pSize = kwargs.get( 'pSize', 3 )
    numIters = kwargs.get( 'numIters', int( 10 ** np.sqrt( pSize - 2 ) ) )
    useShaders = kwargs.get( 'useShaders', False )
     

    # Checking the parameters

    if type( pSize ) is not int:
        raise ValueError("pSize is not an integer")
    if pSize <= 2:
        raise ValueError("pSize must be larger than 2")
    if type( numIters ) is not int:
        raise ValueError("numIters is not an integer")
    if numIters < 1:
        raise ValueError("numIters must be larger than zero")
    if type( useShaders ) is not bool:
        raise ValueError("useShaders is not a bool")
    if useShaders and pSize > 100:
        raise ValueError("pSize cannot be greater than 100 when using shaders")


    # Compute the test

    bestD = np.zeros( ( numIters ) )
    bestS = np.zeros( ( numIters ) )
    rTS = TS[::-1]

    for k in range( numIters ):
        x0 = np.random.uniform( 0.0, 1.0, (pSize) )
        bestD[ k ], bestS[ k ] = _evaluateDistance( x0, np.copy( TS ), np.copy( rTS ), useShaders )

    return np.min( bestD ), bestS[ np.argmin( bestD ) ]




def GetStatistic( TS, **kwargs ):

    """
    Get the statistic according to the Continuous Ordinal Pattern test.

    Parameters
    ----------
    TS : numpy.array
        Time series to be analysed.
    pSize : int
        Size of the pattern. Optional, default: 3.
    numIters : int
        Number of random patterns to be tested. Optional, default: function of the pattern size.
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

    return GetPValue( TS, **kwargs )[ 1 ]

