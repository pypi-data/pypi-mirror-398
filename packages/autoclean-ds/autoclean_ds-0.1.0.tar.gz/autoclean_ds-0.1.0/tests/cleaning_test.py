import pandas as pd
from autoclean import standardize_column_names, detect_missing_values, basic_summary

def test_standardize_column_names():
    df = pd.DataFrame({" First Name ": [1], "AGE ": [2]})
    new_df = standardize_column_names(df)
    assert list(new_df.columns) == ["first_name", "age"]
