import pandas as pd

# -----------------------
# Column Detection Helpers
# -----------------------

def detect_numerical(df):
    """
    Detect numerical columns (int, float).
    """
    return df.select_dtypes(include=["int64", "float64"]).columns.tolist()


def detect_categorical(df, exclude=None):
    """
    Detect categorical columns (object/category),
    excluding datetime columns if provided.
    """
    exclude = exclude or []
    cols = df.select_dtypes(include=["object", "category"]).columns
    return [c for c in cols if c not in exclude]
