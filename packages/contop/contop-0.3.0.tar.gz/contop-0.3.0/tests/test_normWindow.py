import pytest
from pytest import approx

import numpy as np
import copy

import contop as cop



@pytest.mark.parametrize( "length", [ 2, 4, 8, 16, 32 ] )
def test_TS_Does_Not_Change( length ):

    TS = np.random.uniform( 0., 1., (length) )
    TS2 = copy.deepcopy( TS )

    cop.normWindow( TS )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )


@pytest.mark.parametrize( "length", [ 2, 4, 8, 16, 32 ] )
def test_Correct_Normalisation( length ):

    TS = np.random.uniform( -10., 10., (length) )

    TS2 = cop.normWindow( TS )

    assert np.min( TS2 ) == -1, (
        "Minimum is not -1"
    )
    assert np.max( TS2 ) == 1, (
        "Maximum is not 1"
    )

