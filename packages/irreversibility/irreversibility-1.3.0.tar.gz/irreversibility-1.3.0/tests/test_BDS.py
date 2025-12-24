import pytest
from pytest import approx

import numpy as np
import copy

import irreversibility as irr



@pytest.mark.parametrize("max_dim", [2, 3, 4, 5])
@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_TS_Does_Not_Change( max_dim, length ):

    TS = np.random.uniform( 0., 1., (length) )
    TS2 = copy.deepcopy( TS )

    irr.Metrics.BDS.GetPValue( TS, max_dim = max_dim )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )




@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetPValue( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    with pytest.raises(ValueError):
        irr.Metrics.BDS.GetPValue( TS, max_dim = 1. )
    with pytest.raises(ValueError):
        irr.Metrics.BDS.GetPValue( TS, max_dim = -1 )

    with pytest.raises(ValueError):
        irr.Metrics.BDS.GetPValue( TS, distance = -1. )

    irr.Metrics.BDS.GetPValue( TS )




@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetStatistic( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    result = irr.Metrics.BDS.GetStatistic( TS )
    assert isinstance( result, float )




def test_Optimisation():
    """Test the functions for optimising the parameters"""

    from irreversibility.ParameterOptimisation.Opt_BDS import Optimisation

    tsSet = []
    for k in range( 10 ):
        tsSet.append( np.random.uniform( 0., 1., (645) ) )

    Optimisation( tsSet, paramSet = None, criterion = np.median, numProcesses = -1 )

