import pytest
from pytest import approx

import numpy as np
import copy

import irreversibility as irr



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_TS_Does_Not_Change( length ):

    TS = np.random.uniform( 0., 1., (length) )
    TS2 = copy.deepcopy( TS )

    irr.Metrics.CostaIndex.GetPValue( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetPValue( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    with pytest.raises(ValueError):
        irr.Metrics.CostaIndex.GetPValue( TS, tau = 1. )
    with pytest.raises(ValueError):
        irr.Metrics.CostaIndex.GetPValue( TS, tau = -1 )

    with pytest.raises(ValueError):
        irr.Metrics.CostaIndex.GetPValue( TS, method = 'abc' )
    with pytest.raises(ValueError):
        irr.Metrics.CostaIndex.GetPValue( TS, method = 1.0 )

    irr.Metrics.CostaIndex.GetPValue( TS )
    irr.Metrics.CostaIndex.GetPValue( TS, method = 'fraction' )
    irr.Metrics.CostaIndex.GetPValue( TS, method = 'entropy' )



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetStatistic( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    result = irr.Metrics.CostaIndex.GetStatistic( TS )
    assert isinstance( result, float )



def test_Optimisation():
    """Test the functions for optimising the parameters"""

    from irreversibility.ParameterOptimisation.Opt_CostaIndex import Optimisation

    tsSet = []
    for k in range( 10 ):
        tsSet.append( np.random.uniform( 0., 1., (645) ) )

    Optimisation( tsSet, paramSet = None, criterion = np.median, numProcesses = -1 )

