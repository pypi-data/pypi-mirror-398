
"""
Gaspard's estimation of the entropy production for symbolic time series

From:
    Gaspard, P. (2004).
    Time-reversed dynamical entropy and irreversibility in Markovian random processes.
    Journal of statistical physics, 117(3), 599-615.
"""


import numpy as np
import itertools
from scipy.stats import norm
from ..optionalNJIT import optional_njit
from ..warningHandling import warnUser




def _shader_OneSequence( currentS, sequence, n ):

    from wgpu.utils.compute import compute_with_buffers
    m = np.size( sequence )

    A_shape = ( m )
    B_shape = ( n )

    newTS = sequence.astype(np.uint32)

    bindings = {
        0: newTS,
        1: currentS.astype( np.uint32 ),
        3: np.array(A_shape, dtype=np.uint32),
        4: np.array(B_shape, dtype=np.uint32),
    }

    shader_src = """
    @group(0) @binding(0)
    var<storage, read> A: array<u32>;
    @group(0) @binding(1)
    var<storage, read> B: array<u32>;
    @group(0) @binding(2)
    var<storage, read_write> C: array<u32>;

    @group(0) @binding(3)
    var<storage, read> A_shape: array<u32>;

    override n: u32;

    @compute @workgroup_size(1)
    fn main(@builtin(global_invocation_id) gid: vec3<u32>) {

        let m: u32 = A_shape[0];
        var sum1: u32 = 0;
        var sum2: u32 = 0;

        var j: u32 = gid.x;

        C[ j ] = 0;
        C[ j + m ] = 0;

        var counter: u32 = 0;
        for (var i: u32 = 0; i < n; i++) {
            if A[ j + i ] == B[ i ] {
                counter += 1;
            } 
        }
        if counter == n {
            C[ j ] = 1;
        }

        counter = 0;
        for (var i: u32 = 0; i < n; i++) {
            if A[ j + i ] == B[ n - i - 1 ] {
                counter += 1;
            } 
        }
        if counter == n {
            C[ j + m ] = 1;
        }

        return;
    }
    """


    out = compute_with_buffers(
        input_arrays=bindings,
        output_arrays={2: (2*m, "I")},
        shader=shader_src,
        constants={'n': n},
        n=(m-n, 1, 1), 
    )

    C = np.frombuffer(out[2], dtype=np.uint32)
    return ( np.sum( C[ :m ] ), np.sum( C[ m: ] ) )



def _shader_OneSequence_Split( currentS, sequence, n ):

    C = np.array( [ 0., 0. ] )
    if np.size( sequence ) < 60000:
        C += _shader_OneSequence( currentS, sequence, n )
    else:
        startOffset = 0
        while startOffset + 60000 + n < np.size( sequence ):
            C += _shader_OneSequence( currentS, sequence[ startOffset : startOffset + 60000 + n ], n )
            startOffset += 60000
        C += _shader_OneSequence( currentS, sequence[ startOffset : ], n )

    return C




@optional_njit( cache=True, nogil=True )  
def _numba_OneSequence( currentS, sequence, n ):

    count = 0
    for k in range( sequence.shape[0] - n ):
        if np.all( currentS == sequence[ k : (k+n) ] ):
            count += 1

    count2 = 0
    for k in range( sequence.shape[0] - n ):
        if np.all( currentS[::-1] == sequence[ k : (k+n) ] ):
            count2 += 1
            
    return count, count2



def EntropyProduction( sequence, n: int = 3, useShaders: bool = False ):

    """
    Calculate the entropy production, by comparing the frequency of sequences of symbols, and the frequency of their time-reversed versions.
    
    Parameters
    ----------
    sequence : np.ndarray
        Sequence of symbols (or time series) to be analysed. Must be composed of discrete values, i.e. integers.
    n : int
        Length of the sequences of symbols to be analysed. Optional, default: 1.
    useShaders : bool
        Whether to use shaders or only CPU computation. Optional, default: False. 

    Returns
    -------
    float
        Produced entropy.
    """

    symbols = np.unique( sequence )

    H = 0.
    H_r = 0.

    for currentS in itertools.permutations( symbols, r = n ):

        ax = np.array( currentS )

        if useShaders:
            count, count2 = _shader_OneSequence_Split( ax, sequence, n )
        else:
            count, count2 = _numba_OneSequence( ax, sequence, n )

        count /= sequence.shape[0] - n
        count2 /= sequence.shape[0] - n
        
        if count > 0:
            H -= count * np.log( count )

        if count2 > 0:
            H_r -= count * np.log( count2 )

    EntropyProd = ( H_r - H ) / float( n )

    return EntropyProd



def GetPValue( TS, **kwargs ):

    """
    Calculate the Gaspard's test. The p-value is obtained by comparing the obtained entropy production against a set of randomly shuffled time series.
    
    Parameters
    ----------
    TS : np.ndarray
        Sequence of symbols (or time series) to be analysed. Must be composed of discrete values, i.e. integers.
    n : int
        Length of the sequences of symbols to be analysed. Optional, default: 3.
    numRndReps : int
        Number of random shuffled time series used to estimate the p-value. Optional, default: 100.
    useShaders : bool
        Whether to use shaders or only CPU computation. Optional, default: False.
    pValueMethod : string
        Method used to estimate the p-value, including 'proportion' and 'z-score'. Optional, default: 'proportional'.

    Returns
    -------
    float
        Obtained p-value.
    float
        Produced entropy.
    """

    # Setting up the parameters

    n = kwargs.get( 'n', 3 )
    numRndReps = kwargs.get( 'numRndReps', 100 )
    useShaders = kwargs.get( 'useShaders', False )
    pValueMethod = kwargs.get( 'pValueMethod', 'proportion' )


    # Checking the parameters

    if type( TS ) is not np.ndarray:
        raise ValueError( "TS must be a numpy array" )
    if len( np.unique( TS ) ) == np.size( TS ):
        warnUser( "DiscreteMetrics.Gaspard.GetPValue", \
                  "TS doesn't seem to be composed of discrete values" )
    if type( n ) is not int:
        raise ValueError("n is not an integer")
    if n <= 0:
        raise ValueError("n must be larger than 0")
    if n >= np.size( TS ):
        raise ValueError( "n must be smaller than the length of TS" )
    if type( numRndReps ) is not int:
        raise ValueError("numRndReps is not an integer")
    if numRndReps < 0:
        raise ValueError("numRndReps must be zero or positive")
    if type( useShaders ) is not bool:
        raise ValueError("useShaders is not a bool")
    if pValueMethod not in [ 'proportion', 'z-score' ]:
        raise ValueError("pValueMethod not recognised")
        

    # Computing the entropy production

    DS = EntropyProduction( TS, n = n, useShaders = useShaders )

    if numRndReps <= 0:
        return 1.0, DS

    
    # Compute the entropy production for the shuffled versions of the time series

    dsRnd = []
    for k in range( numRndReps ):
        dsRnd.append( EntropyProduction( np.random.permutation( TS ), \
                                         n = n, useShaders = useShaders ) )


    # Extract the p-value

    pValue = 1.0

    if pValueMethod == 'z-score':
        z_score = ( DS - np.mean( dsRnd ) ) / np.std( dsRnd )
        pValue = norm.sf( z_score )
    if pValueMethod == 'proportion':
        pValue = np.sum( DS < np.abs( np.array( dsRnd ) ) ) / numRndReps

    return ( pValue, DS )



def GetStatistic( TS, **kwargs ):

    """
    Calculate the Gaspard's test. 
    
    Parameters
    ----------
    TS : np.ndarray
        Sequence of symbols (or time series) to be analysed. Must be composed of discrete values, i.e. integers.
    n : int
        Length of the sequences of symbols to be analysed. Optional, default: 3.
    useShaders : bool
        Whether to use shaders or only CPU computation. Optional, default: False.

    Returns
    -------
    float
        Produced entropy.
    """


    return GetPValue( TS, numRndReps = 0, **kwargs )[ 1 ]

