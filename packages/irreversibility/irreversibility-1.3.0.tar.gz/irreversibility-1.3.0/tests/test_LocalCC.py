import pytest
from pytest import approx

import numpy as np
import copy

import irreversibility as irr



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_TS_Does_Not_Change( length ):

    TS = np.random.uniform( 0., 1., (length) )
    TS2 = copy.deepcopy( TS )

    irr.Metrics.LocalCC.GetPValue( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )




@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetPValue( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    irr.Metrics.LocalCC.GetPValue( TS )



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetStatistic( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 1., (length) )

    result = irr.Metrics.LocalCC.GetStatistic( TS )
    assert isinstance( result, float )




def test_Optimisation():
    """Test the functions for optimising the parameters"""

    from irreversibility.ParameterOptimisation.Opt_LocalCC import Optimisation

    tsSet = []
    for k in range( 10 ):
        tsSet.append( np.random.uniform( 0., 1., (645) ) )

    Optimisation( tsSet )

