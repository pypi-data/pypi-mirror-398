
import numpy as np
from scipy.stats import ks_2samp

from numba import njit



@njit( cache=True, nogil=True )
def normWindow( ts ):
	
    """
    Normalise a segment of a time series, such the the output is included between -1 and 1.

    This function is optimised via Numba; as a consequence, no parameters are checked. Please make sure that data are correctly passed to it!

    Parameters
    ----------
    ts : numpy.ndarray
        Time series to be normalised.

    Returns
    -------
    numpy.ndarray
        Time series normalised between -1 and 1.

    Raises
    ------
    ValueError
        None.
    """

    newTS = np.copy( ts )
    newTS -= np.min( newTS )
    newTS /= np.max( newTS )
    newTS = ( newTS - 0.5 ) * 2.0
    return newTS




@njit( cache=True, nogil=True )            
def transformTS( ts, patt ):
	
    """
    Transform the input time series, using a predefined COP. The result is thus the function $\phi(t)$ of the original paper, which can then be averaged or postprocessed

    This function is optimised via Numba; as a consequence, no parameters are checked. Please make sure that data are correctly passed to it!

    Parameters
    ----------
    ts : numpy.ndarray
        Time series to be processed.
    patt : numpy.ndarray
        COP to be used in the processing.

    Returns
    -------
    numpy.ndarray
        Processed time series, as the function $\phi(t)$.

    Raises
    ------
    ValueError
        None.
    """
	
    tsL = ts.shape[0]
    phi = np.zeros( ( tsL - patt.shape[0] + 1 ) )
	
    for t in range( tsL - patt.shape[0] + 1 ):
		
        for l in range( patt.shape[0] ):
            
            phi[ t ] += np.abs( normWindow( ts[ t : ( t + patt.shape[0] ) ] )[ l ] - patt[ l ] )

        phi[ t ] = phi[ t ] / patt.shape[0] / 2.0
		
    return phi



def getRandomCOP( embDim: int = 3 ):
	
    """
    Return a random COP of a given embedding dimension.

    Parameters
    ----------
    embDim : int
        Embedding dimension. Must be an integer larger than one. Optional, default: 3.

    Returns
    -------
    numpy.ndarray
        Random COP.

    Raises
    ------
    ValueError
        None.
    """

    pi = np.random.uniform( 0., 1., ( embDim ) )
    pi = normWindow( pi )
    return pi



def distanceCalculation( TS1, TS2, patt ):
	
    """
    Calculate the distance between two time series, or two sets of time series, using a given COP.

    Parameters
    ----------
    TS1 : numpy.ndarray, or list
        Input time series, as a NumPy array, or list of multiple time series. This is the first time series / sets of time series to be compared.
    TS2 : numpy.ndarray, or list
        Input time series, as a NumPy array, or list of multiple time series. This is the second time series / sets of time series to be compared.
    patt : numpy.ndarray
        COP to be used in the processing.

    Returns
    -------
    float
        p-value of the comparison. Results below a significance threshold (e.g. 0.01) indicate that the two time series (or sets thereof) are different in a statistically significant way.
    float
        Statistic of the test; indicates the distance between the two time series (or sets thereof).

    Raises
    ------
    ValueError
        None.
    """
     
    patt = normWindow( patt )

    set1 = []
    set2 = []

    if type( TS1 ) == list and type( TS2 ) == list:
        for ts in TS1:
            new_ts = transformTS( ts, patt ) 
            set1.append( np.nanmean( new_ts ) )

        for ts in TS2:
            new_ts = transformTS( ts, patt ) 
            set2.append( np.nanmean( new_ts ) )

    if type( TS1 ) == np.ndarray and type( TS2 ) == np.ndarray:
        set1 = transformTS( TS1, patt )
        set2 = transformTS( TS2, patt )
        set1[ np.isnan( set1 ) ] = 0.0
        set2[ np.isnan( set2 ) ] = 0.0
        

    res = ks_2samp( set1, set2 )

    return res.pvalue, res.statistic
