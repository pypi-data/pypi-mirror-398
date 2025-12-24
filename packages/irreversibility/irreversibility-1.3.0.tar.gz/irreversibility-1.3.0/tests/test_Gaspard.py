import pytest
from pytest import approx

import numpy as np
import copy

import irreversibility as irr



@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_TS_Does_Not_Change( n ):

    for length in [ 100, 1000, 10000 ]:
        TS = np.random.randint( 0, 2+1, (length) )
        TS2 = copy.deepcopy( TS )
        currentS = np.random.randint( 0, 2+1, (n) )

        irr.DiscreteMetrics.Gaspard._numba_OneSequence( currentS, TS, n = n )
        assert np.sum( TS - TS2 ) == 0, (
            "Time series has been modified, numba"
        )

        irr.DiscreteMetrics.Gaspard._shader_OneSequence_Split( currentS, TS, n = n )
        assert np.sum( TS - TS2 ) == 0, (
            "Time series has been modified, shaders"
        )


@pytest.mark.parametrize("n", [2, 3, 4])
@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_getPsi( n, length ):
    """Test the functions for calculating the entropy production"""

    TS = np.random.randint( 0, 2+1, (length) )
    e_1 = irr.DiscreteMetrics.Gaspard.EntropyProduction( TS, n = n, useShaders = False )
    e_2 = irr.DiscreteMetrics.Gaspard.EntropyProduction( TS, n = n, useShaders = True )
    assert e_1 == approx( e_2, rel=1e-5 ), (
        "The entropy production yielded by the standard approach and shaders' approach do not coincide (length: %d)" % length
    )


def test_GetPValue():
    """Test the functions for calculating the p-value"""

    TS = np.random.randint( 0, 2+1, (100) )

    with pytest.raises(ValueError):
        irr.DiscreteMetrics.Gaspard.GetPValue( TS, n = 1. )
    with pytest.raises(ValueError):
        irr.DiscreteMetrics.Gaspard.GetPValue( TS, n = -1. )

    with pytest.raises(ValueError):
        irr.DiscreteMetrics.Gaspard.GetPValue( TS, numRndReps = 10. )
    with pytest.raises(ValueError):
        irr.DiscreteMetrics.Gaspard.GetPValue( TS, numRndReps = -1 )

    with pytest.raises(ValueError):
        irr.DiscreteMetrics.Gaspard.GetPValue( TS, pValueMethod = 'a' )
    irr.DiscreteMetrics.Gaspard.GetPValue( TS, pValueMethod = 'proportion' )
    irr.DiscreteMetrics.Gaspard.GetPValue( TS, pValueMethod = 'z-score' )



