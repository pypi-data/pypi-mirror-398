import pytest
from pytest import approx

import numpy as np
import copy

import irreversibility as irr



@pytest.mark.parametrize("pSize", [3, 4, 5])
@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_TS_Does_Not_Change( pSize, length ):

    x0 = np.random.uniform( 0.0, 1.0, (pSize) )
    TS = np.random.uniform( 0., 1., ( length ) )
    rTS = TS[::-1]
    TS2 = copy.deepcopy( TS )

    irr.Metrics.COP._evaluateDistance( x0, TS, rTS, useShaders = False )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified, numba"
    )

    irr.Metrics.COP._evaluateDistance( x0, TS, rTS, useShaders = True )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified, shaders"
    )


@pytest.mark.parametrize("pSize", [3, 4, 5])
@pytest.mark.parametrize("length", [ 100, 1000, 10000, 100000 ])
def test_tranfTS( pSize, length ):
    """Test the functions for calculating Psi"""

    TS = np.random.uniform( 0., 1., ( length ) )
    patt = np.random.uniform( 0., 1., ( pSize ) )
    patt = irr.Metrics.COP._numba_normWindow( patt )

    psi_1 = irr.Metrics.COP._shader_tranfTS( TS, patt )
    psi_2 = irr.Metrics.COP._numba_tranfTS( TS, patt )
    assert np.sum( psi_1 ) == approx( np.sum( psi_2 ), rel=1e-3 ), (
        "Distance yielded by the standard approach and shaders' approach do not coincide (length: %d)" % length
    )


@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetPValue( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    with pytest.raises(ValueError):
        irr.Metrics.COP.GetPValue( TS, pSize = 1. )
    with pytest.raises(ValueError):
        irr.Metrics.COP.GetPValue( TS, pSize = -1 )

    with pytest.raises(ValueError):
        irr.Metrics.COP.GetPValue( TS, numIters = 10. )
    with pytest.raises(ValueError):
        irr.Metrics.COP.GetPValue( TS, numIters = -1 )

    irr.Metrics.COP.GetPValue( TS )



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetStatistic( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    result = irr.Metrics.COP.GetStatistic( TS )
    assert isinstance( result, float )




def test_Optimisation():
    """Test the functions for optimising the parameters"""

    from irreversibility.ParameterOptimisation.Opt_COP import Optimisation

    tsSet = []
    for k in range( 10 ):
        tsSet.append( np.random.uniform( 0., 1., (645) ) )

    Optimisation( tsSet, paramSet = None, criterion = np.median, numProcesses = -1, useShaders = False )
    Optimisation( tsSet, paramSet = None, criterion = np.median, numProcesses = -1, useShaders = True )

