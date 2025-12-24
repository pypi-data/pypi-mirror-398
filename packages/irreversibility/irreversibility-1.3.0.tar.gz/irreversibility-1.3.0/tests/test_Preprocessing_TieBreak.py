import pytest
from pytest import approx

import numpy as np
import copy



@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_Noise_TS_Does_Not_Change( length ):

    TS = np.random.uniform( 0., length, (length) )
    TS2 = copy.deepcopy( TS )

    from irreversibility.Preprocessing import TieBreak
    TS3 = TieBreak.Noise( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )


@pytest.mark.parametrize("length", [ 10, 20, 40, 80, 160 ])
def test_Noise_TS_Size_Does_Not_Change( length ):

    TS = np.random.uniform( 0., length, (length) )

    from irreversibility.Preprocessing import TieBreak
    TS2 = TieBreak.Noise( TS )
    assert np.size( TS ) == np.size( TS2 ), (
        "Time series length has been modified"
    )

    TS = np.floor( TS )
    TS2 = TieBreak.Noise( TS )
    assert np.size( TS ) == np.size( TS2 ), (
        "Time series length has been modified"
    )


@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_Noise_Ranking_Does_Not_Change( length ):

    TS = np.random.uniform( 0., length, (length) )

    from irreversibility.Preprocessing import TieBreak
    TS2 = TieBreak.Noise( TS )

    assert np.sum( np.argsort( TS ) - np.argsort( TS2 ) ) == 0, (
        "Rankings have been modified"
    )



# ------------------------------------------------------------------


@pytest.mark.parametrize("length", [ 100, 1000, 10000 ])
def test_NoiseOnTies_TS_Does_Not_Change( length ):

    TS = np.random.uniform( 0., length, (length) )
    TS2 = copy.deepcopy( TS )

    from irreversibility.Preprocessing import TieBreak
    TS3 = TieBreak.NoiseOnTies( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )
    assert np.sum( TS - TS3 ) == 0, (
        "Time series has been modified"
    )



@pytest.mark.parametrize("length", [ 10, 20, 40, 80, 160 ])
def test_NoiseOnTies_TS_Size_Does_Not_Change( length ):

    TS = np.random.uniform( 0., length, (length) )

    from irreversibility.Preprocessing import TieBreak
    TS2 = TieBreak.NoiseOnTies( TS )
    assert np.size( TS ) == np.size( TS2 ), (
        "Time series length has been modified"
    )

    TS = np.floor( TS )
    TS2 = TieBreak.NoiseOnTies( TS )
    assert np.size( TS ) == np.size( TS2 ), (
        "Time series length has been modified"
    )



def test_NoiseOnTies_ManualTest( ):

    TS = np.array( [ 0, 1, 1, 2 ], dtype = float )

    from irreversibility.Preprocessing import TieBreak
    TS2 = TieBreak.NoiseOnTies( TS )
    assert np.sum( TS2[ 1 ] - TS2[ 2 ] ) == 0, (
        "Tie not broken"
    )

    TS = np.array( [ 1, 2, 3, 4 ], dtype = float )
    TS2 = TieBreak.NoiseOnTies( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )

