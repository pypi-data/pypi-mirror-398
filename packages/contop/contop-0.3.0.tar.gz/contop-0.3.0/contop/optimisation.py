
import numpy as np

from .core import normWindow, transformTS, distanceCalculation



def optimiseRandom( TS1, TS2, numPatterns: int = 100, embDim: int = 4 ):
	
    """
    Optimisation of the best COP to discriminate between two time series using random trials. A set of COPs are created, randomly drawn from a uniform distribution, for then selecting the one yielding the best separation.

    Parameters
    ----------
    TS1 : numpy.ndarray
        Input time series, as a NumPy array. This is the first time series to be compared.
    TS2 : numpy.ndarray
        Input time series, as a NumPy array. This is the second time series / sets of time series to be compared.
    numPatterns : int
        Number of random COPs to be tested. Optional, default: 100.
    embDim : int
        Embedding dimension, i.e. size of each COP. Optional, default: 4

    Returns
    -------
    numpy.ndarray
        COP resulting the the maximum difference between the two time series.
    float
        Best (i.e. smallest) p-value of the comparison. Results below a significance threshold (e.g. 0.01) indicate that the two time series are different in a statistically significant way, using the previously obtained COP.
    float
        Statistic of the test, corresponding to the optimal p-value (as reported above); indicates the distance between the two time series.

    Raises
    ------
    ValueError
        None.
    """

    bestPValue = 1.0
    bestPattern = []
    bestStatistic = []

    for _ in range( numPatterns ):

        patt = np.random.uniform( 0., 1., ( embDim ) )
        pValue, statistic = distanceCalculation( TS1, TS2, patt )

        if pValue < bestPValue:
            bestPValue = pValue
            bestPattern = patt
            bestStatistic = statistic

    return bestPattern, bestPValue, bestStatistic

        
