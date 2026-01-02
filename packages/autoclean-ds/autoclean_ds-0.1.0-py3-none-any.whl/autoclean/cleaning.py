import pandas as pd
import numpy as np

# -------------------------
# BASIC CLEANING UTILITIES
# -------------------------

def standardize_column_names(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df


def remove_duplicates(df):
    return df.drop_duplicates().reset_index(drop=True)


def drop_empty_columns(df):
    return df.dropna(axis=1, how="all")


def detect_constant_columns(df):
    return [c for c in df.columns if df[c].nunique(dropna=True) <= 1]


# -------------------------
# MISSING VALUE HANDLING
# -------------------------

def handle_missing(df, numeric_strategy="median", cat_strategy="mode"):
    df = df.copy()

    for col in df.columns:
        if df[col].isna().sum() == 0:
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            if numeric_strategy == "median":
                df[col] = df[col].fillna(df[col].median())

        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].interpolate(method="time", limit_direction="both")

        else:
            mode = df[col].mode()
            df[col] = df[col].fillna(mode.iloc[0] if not mode.empty else "Unknown")

    return df


# -------------------------
# OUTLIER HANDLING
# -------------------------

def remove_outliers(df, factor=1.5):
    df = df.copy()
    removed = 0

    for col in df.select_dtypes(include=["int64", "float64"]).columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1

        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR

        before = len(df)
        df = df[(df[col] >= lower) & (df[col] <= upper)]
        removed += before - len(df)

    return df, removed
