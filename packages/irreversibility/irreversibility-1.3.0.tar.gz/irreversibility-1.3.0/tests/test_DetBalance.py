import pytest
from pytest import approx

import numpy as np
import copy

import irreversibility as irr
from irreversibility.DiscreteMetrics.DetBalance import GetPValue, GetPValue_and_ZScore, GetStatistic



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_TS_Does_Not_Change( length ):

    TS = np.random.uniform( 0., 10., (length) )
    TS = np.array( TS, dtype = int )
    TS2 = copy.deepcopy( TS )

    GetPValue( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )
    GetPValue_and_ZScore( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )
    GetStatistic( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetPValue( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 10., (length) )
    TS = np.array( TS, dtype = int )

    GetPValue( TS )



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_GetStatistic( length ):
    """Test the functions for calculating the p-value"""

    TS = np.random.uniform( 0., 10., (length) )
    TS = np.array( TS, dtype = int )

    result = GetStatistic( TS )
    assert isinstance( result, float )



