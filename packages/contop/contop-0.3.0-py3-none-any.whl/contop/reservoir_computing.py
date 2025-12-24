
# Importing of classification models
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from scipy.stats import binomtest
import numpy as np

from .core import normWindow, transformTS





def ExtractAllFeatures( TS_f, TS_r, embDim = 4, numPatterns = 10, udPatterns = [] ):

    Features = []
    Class = []

    if len( udPatterns ) > 0:
        patterns = udPatterns
        embDim = len( patterns[ 0 ] )
        numPatterns = len( udPatterns )
    else:
        patterns = []
        for k in range( numPatterns ):
            ptn = np.random.uniform( 0.0, 1.0, ( embDim ) )
            ptn = normWindow( ptn )
            patterns.append( ptn )


    for k in range( np.size( TS_f ) - embDim ):
        Features.append( [] )
        Class.append( 0 )
        Features.append( [] )
        Class.append( 1 )

    for ptn in patterns:

        newTS_f = transformTS( TS_f, ptn )
        newTS_r = transformTS( TS_r, ptn )
        for k in range( np.size( TS_f ) - embDim ):
            Features[ 2*k ].append( newTS_f[ k ] )
            Features[ 2*k + 1 ].append( newTS_r[ k ] )


    Features = np.array( Features )
    Features[ np.isnan( Features ) ] = 0.

    Class = np.array( Class )

    return patterns, Features, Class




def testingReservoirComputing( TS, TS_null, udPatterns = [], numPatterns: int = 100, embDim: int = 4, maxFeatures: int = 10, model: str = 'rf', getPattImportance: bool = False ):


    """
    Test assessing whether a time series, is the result of the same dynamical process as the one that generated a reference time series - which constitutes the null hypothesis of the test. This assessment is done through a reservoir computing approach, in which multiple COPs are tested, and the results are used to train a Machine Learning classification model.

    Parameters
    ----------
    TS : numpy.ndarray
        Input time series, as a NumPy array, to be analysed.
    TS_null : numpy.ndarray
        Time series used as null hypothesis for the test.
    udPatterns : list of numpy.ndarray
        List of user-defined patterns, to be used in the analysis. Setting this element overloads the following two options, as random COPs will not be generated. Note that the patterns here specified must be normalised. Optional, default: [].
    numPatterns : int
        Number of random COPs that are tested. Optional, default: 100.
    embDim : int
        Embedding dimension, i.e. size of each COP. Optional, default: 4.
    maxFeatures : int
        Maximum number of features (i.e. of values obtained through COPs) that can be used at the same time in the classification model. Optional, default: 10.
    model : str
        String defining the Machine Learning model to be used in the classification. Options include: 'rf' for Random Forest; 'gb' for Gradient Boosting; 'svm' for Support Vector Machine; 'knn' for k-nearest neighbours. Optional, default: 'rf'.
    getPattImportance : bool
        If True, return an estimation of the importance of each pattern. This could be used to analyse which feature of the time series is relevant, or to create smaller models. This is only available for Random Forest and Gradient Boosting models. Optional, default: False

    Returns
    -------
    numpy.ndarray
        Set of COPs used to calculate the test.
    float
        p-value of the comparison. Results below a significance threshold (e.g. 0.01) indicate that the time series (or sets thereof) are different from those constituting the null model.
    float
        Statistic of the test, indicating how different are the time series. This distance corresponds to the accuracy of the classification performed by the Random Forest model, and is therefore defined between zero and one.
    numpy.ndarray
        If getPattImportance is True, vector with the importance of each feature.

    Raises
    ------
    ValueError
        None.
    """

    if model not in [ 'rf', 'gb', 'svm', 'knn' ]:
        raise ValueError( "The specified model is not valid." )
    if getPattImportance and model not in [ 'rf', 'gb' ]:
        raise ValueError( "The estimation of the importance of patterns is only available for Random Forest and Gradient Boosting." )


    patterns, Features, Class = \
            ExtractAllFeatures( 
                np.copy( TS ),
                TS_null,
                embDim = embDim,
                numPatterns = numPatterns,
                udPatterns = udPatterns
            )

    reorder = np.random.permutation( np.size( Class ) )
    Features = Features[ reorder, : ]
    Class = Class[ reorder ]

    clf = None
    if model == 'rf':
        clf = RandomForestClassifier( n_estimators = 1000, \
                                    max_depth = 2, max_features = maxFeatures, min_samples_split = 10 )
    if model == 'gb':
        clf = GradientBoostingClassifier( n_estimators = 1000, \
                                    max_depth = 2, max_features = maxFeatures, min_samples_split = 10 )
    if model == 'svm':
        clf = SVC()
    if model == 'knn':
        clf = KNeighborsClassifier( n_neighbors = 5 )

    kf = KFold( n_splits = 10, shuffle = True )
    scores = cross_val_score( clf, Features, Class, cv = kf )
    finalScore = np.mean( scores )

    numTrials = int( np.size( Features, 0 ) * 5 )
    numSuccesses = int( numTrials * finalScore )

    result = binomtest( numSuccesses, numTrials, \
                        p = 0.5, alternative = 'greater' )

    pV = result.pvalue
    stat = finalScore
    
    if getPattImportance:
        clf.fit( Features, Class )
        pattImp = clf.feature_importances_
        return patterns, pV, stat, pattImp

    return patterns, pV, stat







def testingReservoirComputing_PatternsOpt( TS, TS_null, numInitPatterns: int = 1000, numFinalPatterns: int = 100, embDim: int = 4, maxFeatures: int = 10, model: str = 'rf', getPattImportance: bool = False ):

    initModel = model
    if initModel not in [ 'rf', 'gb' ]:
        initModel = 'gb'

    patterns, pV, stat, pattImp = testingReservoirComputing( 
        TS, 
        TS_null, 
        numPatterns = numInitPatterns, 
        embDim = embDim, 
        maxFeatures = maxFeatures, 
        model = initModel, 
        getPattImportance = True 
        )
    
    udPatternsNew = []
    for k in range( numFinalPatterns ):
        udPatternsNew.append( patterns[ np.argsort( pattImp )[ ::-1 ][ k ] ] )

    _, pV2, stat2 = testingReservoirComputing( 
        TS, 
        TS_null, 
        udPatterns = udPatternsNew,
        maxFeatures = maxFeatures, 
        model = model
        )
    
    return udPatternsNew, pV2, stat2

