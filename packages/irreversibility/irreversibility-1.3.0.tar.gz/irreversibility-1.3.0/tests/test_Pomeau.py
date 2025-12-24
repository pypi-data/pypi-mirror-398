import pytest
from pytest import approx

import numpy as np
import copy

import irreversibility as irr



@pytest.mark.parametrize("tau", [1, 2, 3, 4, 5])
def test_TS_Does_Not_Change( tau ):

    for length in [ 100, 1000, 10000 ]:
        TS = np.random.uniform( 0., 1., ( length ) )
        TS2 = copy.deepcopy( TS )

        irr.Metrics.Pomeau._numba_getPsi( TS, tau = tau )
        assert np.sum( TS - TS2 ) == 0, (
            "Time series has been modified, numba"
        )

        irr.Metrics.Pomeau._shader_getPsi( TS, tau = tau )
        assert np.sum( TS - TS2 ) == 0, (
            "Time series has been modified, shaders"
        )


@pytest.mark.parametrize("tau", [1, 2, 3])
def test_getPsi( tau ):
    """Test the functions for calculating Psi"""

    TS = np.array( range( 100 ) ) / 100.
    correctPsi = [ 
        0.,
        0.003166666,
        0.006225333,
        0.009166999
    ]

    psi_1 = irr.Metrics.Pomeau._numba_getPsi( TS, tau = tau )
    assert psi_1 == approx( correctPsi[ tau ] ), (
        "Psi yielded by the standard approach is not correct"
    )

    psi_2 = irr.Metrics.Pomeau._shader_getPsi( TS, tau = tau )
    assert psi_1 == approx( psi_2 ), (
        "Psi yielded by the standard approach and shaders' approach do not coincide"
    )

    for length in [ 100, 1000, 10000 ]:
        TS = np.random.uniform( 0., 1., ( length ) )
        psi_1 = irr.Metrics.Pomeau._numba_getPsi( TS, tau = tau )
        psi_2 = irr.Metrics.Pomeau._shader_getPsi( TS, tau = tau )
        assert psi_1 == approx( psi_2, rel=1e-3 ), (
            "Psi yielded by the standard approach and shaders' approach do not coincide (length: %d)" % length
        )


@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetPValue( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetPValue( TS, tau = 1. )
    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetPValue( TS, tau = -1. )

    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetPValue( TS, numRndReps = 10. )
    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetPValue( TS, numRndReps = -1 )

    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetPValue( TS, pValueMethod = 'a' )
    irr.Metrics.Pomeau.GetPValue( TS, pValueMethod = 'proportion' )
    irr.Metrics.Pomeau.GetPValue( TS, pValueMethod = 'z-score' )



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetStatistic( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    result = irr.Metrics.Pomeau.GetStatistic( TS )
    assert isinstance( result, float )



def test_GetStatistic():
    """Test the functions for calculating Psi"""

    TS = np.random.uniform( 0., 1., ( 100 ) )

    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetStatistic( TS, tau = 1. )
    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetStatistic( TS, tau = -1. )

    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetPValue( TS, numRndReps = 10. )
    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetPValue( TS, numRndReps = -1 )

    with pytest.raises(ValueError):
        irr.Metrics.Pomeau.GetPValue( TS, pValueMethod = 'a' )
    irr.Metrics.Pomeau.GetPValue( TS, pValueMethod = 'proportion' )
    irr.Metrics.Pomeau.GetPValue( TS, pValueMethod = 'z-score' )


def test_Optimisation():
    """Test the functions for optimising the parameters"""

    from irreversibility.ParameterOptimisation.Opt_Pomeau import Optimisation

    tsSet = []
    for k in range( 10 ):
        tsSet.append( np.random.uniform( 0., 1., (6453) ) )

    Optimisation( tsSet, paramSet = None, criterion = np.median, numProcesses = -1, useShaders = False )
    Optimisation( tsSet, paramSet = None, criterion = np.median, numProcesses = -1, useShaders = True )

