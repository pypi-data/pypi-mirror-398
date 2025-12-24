import pytest
from pytest import approx

import numpy as np
import copy
import math



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_PermPatterns_TS_Does_Not_Change( length ):

    TS = np.random.uniform( 0., length, (length) )
    TS2 = copy.deepcopy( TS )

    from irreversibility.Preprocessing import PermPatterns
    TS3, _ = PermPatterns.TimeSeriesToPermPatterns( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )


@pytest.mark.parametrize("length", [ 10, 20, 40, 80, 160 ])
@pytest.mark.parametrize("pSize", [ 3, 4, 5 ])
def test_PermPatterns_TS_Size_Does_Not_Change( length, pSize ):

    TS = np.random.uniform( 0., length, (length) )

    from irreversibility.Preprocessing import PermPatterns
    TS2, _ = PermPatterns.TimeSeriesToPermPatterns( TS, pSize = pSize )
    assert np.size( TS ) == np.size( TS2 ) + pSize, (
        "Time series length has been modified"
    )

    TS = np.floor( TS )
    TS2, _ = PermPatterns.TimeSeriesToPermPatterns( TS, pSize = pSize )
    assert np.size( TS ) == np.size( TS2 ) + pSize, (
        "Time series length has been modified"
    )


@pytest.mark.parametrize("pSize", [ 3, 4, 5 ])
def test_PermPatterns_Size_PP( pSize ):

    length = 200
    TS = np.random.uniform( 0., length, (length) )

    from irreversibility.Preprocessing import PermPatterns
    TS2, PP = PermPatterns.TimeSeriesToPermPatterns( TS, pSize = pSize )

    assert np.size( PP, 1 ) == pSize, (
        "PermPatt size not coherent"
    )

    assert np.size( PP, 0 ) == math.factorial( pSize ), (
        "PermPatt size not coherent"
    )



def test_PermPatterns_Manual():

    from irreversibility.Preprocessing import PermPatterns

    TS = np.array( [ 1., 2., 3., 4., 5., 6. ] )
    TS2, PP = PermPatterns.TimeSeriesToPermPatterns( TS, pSize = 3, overlapping = True )

    assert np.sum( TS2 > 0 ) == 0, (
        "Time series not correctly transformed"
    )
