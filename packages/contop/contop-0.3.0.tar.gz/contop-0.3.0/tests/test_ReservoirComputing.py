import pytest
from pytest import approx

import numpy as np
import copy

import contop as cop



@pytest.mark.parametrize( "numPatt", [ 4, 8, 16, 32 ] )
def test_Patterns_Are_Preserved( numPatt ):

    TS = np.random.uniform( 0., 1., ( 100 ) )
    TS_Rnd = np.random.permutation( TS )

    udPatterns = []
    for k in range( numPatt ):
        ptn = np.random.uniform( 0., 1., ( 4 ) )
        ptn = cop.normWindow( ptn )
        udPatterns.append( ptn )

    newPatterns, pV1, stat1 = cop.testingReservoirComputing( 
                                    TS,
                                    TS_Rnd,
                                    udPatterns = udPatterns,
                                )
    
    assert len( udPatterns ) == len( newPatterns ), (
        "The number of patterns has changed"
    )

    for k in range( numPatt ):
        assert np.sum( udPatterns[ k ] - newPatterns[ k ] ) == 0, (
            "A pattern has changed"
        )
