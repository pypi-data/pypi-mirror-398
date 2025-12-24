import pytest
from pytest import approx

import numpy as np
import copy

import contop as cop



@pytest.mark.parametrize( "length", [ 4, 8, 16, 32, 64, 128 ] )
def test_TS_Does_Not_Change( length ):

    TS = np.random.uniform( 0., 1., (length) )
    pi = np.random.uniform( 0., 1., (4) )
    pi = cop.normWindow( pi )
    TS2 = copy.deepcopy( TS )
    pi2 = copy.deepcopy( pi )

    cop.transformTS( TS, pi )
    assert np.sum( TS - TS2 ) == 0, (
        "Time series has been modified"
    )
    assert np.sum( pi - pi2 ) == 0, (
        "The COP has been modified"
    )



def test_Manual_Values( ):

    ts = np.array( [ 0, 1, 2 ], dtype = float )
    pi = np.array( [ -1, 0, 1 ], dtype = float )

    newTS = cop.transformTS( ts, pi )
    assert newTS[ 0 ] == 0., (
        "Incorrect transformation"
    )

    ts = np.array( [ 2, 1, 0 ], dtype = float )
    newTS = cop.transformTS( ts, pi )
    assert newTS[ 0 ] == 2. / 3., (
        "Incorrect transformation"
    )




@pytest.mark.parametrize( "length", [ 8, 16, 32, 64, 128, 256 ] )
@pytest.mark.parametrize( "cop_l", [ 3, 4, 5 ] )
def test_Manual_Values_Zero_Distance( length, cop_l ):

    ts = np.arange( 0., length )

    pi = np.arange( 0, cop_l, dtype = float )
    pi = cop.normWindow( pi )

    newTS = cop.transformTS( ts, pi )
    assert np.size( newTS ) == length - cop_l + 1, (
        "Incorrect transformation"
    )
    assert np.sum( newTS == 0. ) == np.size( newTS ), (
        "Incorrect transformation"
    )


@pytest.mark.parametrize( "length", [ 8, 16, 32, 64, 128, 256 ] )
@pytest.mark.parametrize( "cop_l", [ 2 ] )
def test_Manual_Values_Max_Distance( length, cop_l ):

    ts = np.arange( 0., length )

    pi = np.arange( 0, cop_l, dtype = float )
    pi = cop.normWindow( pi )
    pi = 1. - pi

    newTS = cop.transformTS( ts, pi )
    assert np.size( newTS ) == length - cop_l + 1, (
        "Incorrect transformation"
    )
    assert np.sum( newTS == 1. ) == np.size( newTS ), (
        "Incorrect transformation"
    )
