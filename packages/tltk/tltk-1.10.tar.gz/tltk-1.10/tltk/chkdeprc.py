import warnings

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn_crfsuite import CRF
from sklearn.decomposition import PCA

'''
from sklearn.pipeline import Pipeline

'''

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    # Code that triggers a DeprecationWarning
    PCA()
    if len(w) > 0:
        # A DeprecationWarning was raised
        print("Deprecated function")
