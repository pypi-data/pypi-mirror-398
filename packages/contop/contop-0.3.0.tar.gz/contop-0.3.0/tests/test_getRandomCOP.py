import pytest
from pytest import approx

import numpy as np
import copy

import contop as cop



@pytest.mark.parametrize( "length", [ 2, 3, 4, 5, 6, 7, 8, 9 ] )
def test_COP_Is_OK( length ):

    pi = cop.getRandomCOP( length )

    assert np.size( pi ) == length, (
        "COP of incorrect size"
    )
    assert np.min( pi ) == -1., (
        "COP minimum is wrong"
    )
    assert np.max( pi ) == 1., (
        "COP maximum is wrong"
    )


