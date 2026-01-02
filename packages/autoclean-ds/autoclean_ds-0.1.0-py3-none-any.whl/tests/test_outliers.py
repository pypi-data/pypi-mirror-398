import pandas as pd
from autoclean.engine import AutoClean

def test_outliers_iqr():
    df = pd.DataFrame({"age": [10, 12, 11, 1000]})
    ac = AutoClean(df)

    cleaned = ac.remove_outliers(method="iqr")

    # Outlier (1000) should be removed
    assert cleaned["age"].max() < 1000


def test_outliers_no_outliers():
    df = pd.DataFrame({"age": [10, 11, 12, 13]})
    ac = AutoClean(df)

    cleaned = ac.remove_outliers(method="iqr")

    # All rows remain
    assert cleaned.shape[0] == 4
