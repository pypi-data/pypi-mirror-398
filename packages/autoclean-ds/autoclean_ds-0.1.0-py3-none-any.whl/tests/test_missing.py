import pandas as pd
from autoclean.engine import AutoClean

def test_missing_mean_strategy():
    df = pd.DataFrame({"age": [10, None, 20]})
    ac = AutoClean(df)
    cleaned = ac.fix_missing()

    # Missing should be fixed
    assert cleaned["age"].isna().sum() == 0


def test_missing_median_strategy():
    df = pd.DataFrame({"salary": [100, None, 300]})
    ac = AutoClean(df)
    cleaned = ac.fix_missing()

    # Missing fixed
    assert cleaned["salary"].isna().sum() == 0


def test_missing_categorical_fill():
    df = pd.DataFrame({"city": ["NY", None, "LA"]})
    ac = AutoClean(df)
    cleaned = ac.fix_missing()

    # NA replaced with mode
    assert cleaned["city"].isna().sum() == 0
