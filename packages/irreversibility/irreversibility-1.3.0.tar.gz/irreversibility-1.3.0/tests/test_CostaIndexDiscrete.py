import pytest
from pytest import approx

import numpy as np
import copy

import irreversibility as irr



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_TS_Does_Not_Change( length ):

    TS = np.random.uniform( 0., 10., (length) )
    TS = np.array( TS, dtype = int )
    TS2 = copy.deepcopy( TS )

    irr.DiscreteMetrics.CostaIndex.GetPValue( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetPValue( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 10., (length) )
    TS = np.array( TS, dtype = int )

    with pytest.raises(ValueError):
        irr.DiscreteMetrics.CostaIndex.GetPValue( TS, tau = 1. )
    with pytest.raises(ValueError):
        irr.DiscreteMetrics.CostaIndex.GetPValue( TS, tau = -1 )

    irr.DiscreteMetrics.CostaIndex.GetPValue( TS )



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetStatistic( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 10., (length) )
    TS = np.array( TS, dtype = int )

    result = irr.DiscreteMetrics.CostaIndex.GetStatistic( TS )
    assert isinstance( result, float )



def test_Optimisation():
    """Test the functions for optimising the parameters"""

    from irreversibility.ParameterOptimisation.Opt_CostaIndexDiscrete import Optimisation

    tsSet = []
    for k in range( 10 ):
        TS = np.random.uniform( 0., 10., (645) )
        TS = np.array( TS, dtype = int )
        tsSet.append( TS )

    Optimisation( tsSet, paramSet = None, criterion = np.median, numProcesses = -1 )

