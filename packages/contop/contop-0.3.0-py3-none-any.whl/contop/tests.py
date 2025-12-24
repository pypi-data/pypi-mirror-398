
import numpy as np

from .optimisation import optimiseRandom



def testingRandomness( TS, numPatterns: int = 100, embDim: int = 4 ):

    """
    Test assessing the random nature of a time series. The time series composing the input aisre randomly shuffled, for then assessing the distance between the original version and the shuffled one. If the distance is not null, we can conclude that the underlying time series are not random.

    Parameters
    ----------
    TS : numpy.ndarray
        Input time series, as a NumPy array, to be analysed.
    numPatterns : int
        Number of random COPs that are tested. Optional, default: 100.
    embDim : int
        Embedding dimension, i.e. size of each COP. Optional, default: 4

    Returns
    -------
    numpy.ndarray
        COP representing the maximum difference between the original time series and its randomly shuffled version.
    float
        Best (i.e. smallest) p-value of the comparison. Results below a significance threshold (e.g. 0.01) indicate that the time series is different from their random counterparts, using the previously obtained COP; and therefore that are not random.
    float
        Statistic of the test, corresponding to the optimal p-value (as reported above); indicates the distance between the time series and its random counterpart.

    Raises
    ------
    ValueError
        None.
    """


    TS_Null = np.random.permutation( TS )
    
    bestPattern, bestPValue, bestStatistic = \
        optimiseRandom( TS, \
                        TS_Null, \
                        numPatterns = numPatterns, \
                        embDim = embDim )

    return bestPattern, bestPValue, bestStatistic



def testingIrreversibility( TS, numPatterns: int = 100, embDim: int = 4 ):

    """
    Test assessing the irreversible nature of a time series. The time series composing the input is reversed, for then assessing the distance between the original version and the time-reversed one. If the distance is not null, we can conclude that the underlying time series is not time reversible.

    While this function is included here for the sake of completeness, we recommend referring to the full implementation included in the "irreversibility" library: https://gitlab.com/MZanin/irreversibilitytestslibrary

    Parameters
    ----------
    TS : numpy.ndarray, or list
        Input time series, as a NumPy array, to be analysed.
    numPatterns : int
        Number of random COPs that are tested. Optional, default: 100.
    embDim : int
        Embedding dimension, i.e. size of each COP. Optional, default: 4

    Returns
    -------
    numpy.ndarray
        COP representing the maximum difference between the original time series and its time-reversed version.
    float
        Best (i.e. smallest) p-value of the comparison. Results below a significance threshold (e.g. 0.01) indicate that the time series is different from their time-reversed counterparts, using the previously obtained COP; and therefore that is not time reversible.
    float
        Statistic of the test, corresponding to the optimal p-value (as reported above); indicates the distance between the time series and its time-reversed counterpart.

    Raises
    ------
    ValueError
        None.
    """


    TS_Null = np.copy( TS[::-1] )

    
    bestPattern, bestPValue, bestStatistic = \
        optimiseRandom( TS, \
                        TS_Null, \
                        numPatterns = numPatterns, \
                        embDim = embDim )

    return bestPattern, bestPValue, bestStatistic
