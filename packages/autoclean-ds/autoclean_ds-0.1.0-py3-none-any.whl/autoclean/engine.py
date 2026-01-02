import pandas as pd
import numpy as np

from .utils import (
    detect_numerical,
    detect_categorical,
)

from .cleaning import (
    standardize_column_names,
    remove_duplicates,
    drop_empty_columns,
    handle_missing,
    remove_outliers,
    detect_constant_columns,
)

from .report import generate_report


class AutoClean:
    """
    AutoClean Strategy Engine

    - Analyzes dataset
    - Chooses cleaning strategies
    - Executes cleaning pipeline
    - Produces before/after report
    """

    def __init__(self, df, config=None, verbose=True):
        self.df = df.copy()
        self.verbose = verbose

        self.config = config if config else {
            "missing_threshold": 0.40,
            "outlier_method": "iqr",
            "iqr_factor": 1.5,
        }

        # Metadata
        self.meta = {"numerical": [], "categorical": [], "datetime": []}

        # Analysis containers
        self.analysis = {
            "missing": {},
            "outliers": {},
            "dtypes": {},
        }

        # Reports
        self.missing_report = {}
        self.outlier_report = {}

        # Metrics
        self.metrics = {
            "missing_fixed": 0,
            "columns_dropped": 0,
            "outliers_removed": 0,
        }

    # ------------------------
    # ANALYSIS
    # ------------------------

    def analyze_missing(self):
        missing = self.df.isna().mean().to_dict()
        self.analysis["missing"] = missing
        self.missing_report = missing
        return missing

    def analyze_dtypes(self):
        self.meta["numerical"] = detect_numerical(self.df)
        self.meta["categorical"] = detect_categorical(self.df)
        self.meta["datetime"] = self.detect_datetime()

        dtype_report = {
            "numerical": self.meta["numerical"],
            "categorical": self.meta["categorical"],
            "datetime": self.meta["datetime"],
        }

        self.analysis["dtypes"] = dtype_report
        return dtype_report

    def analyze_outliers(self):
        outliers = {}

        for col in self.meta["numerical"]:
            series = self.df[col].dropna()
            if series.empty:
                outliers[col] = 0
                continue

            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1

            lower = Q1 - self.config["iqr_factor"] * IQR
            upper = Q3 + self.config["iqr_factor"] * IQR

            outliers[col] = int(((series < lower) | (series > upper)).sum())

        self.analysis["outliers"] = outliers
        self.outlier_report = outliers
        return outliers

    # ------------------------
    # SAFE DATETIME DETECTION
    # ------------------------

    def detect_datetime(self):
        datetime_cols = []
        skip_keywords = [
            "id", "code", "comment", "note", "text",
            "desc", "message", "info"
        ]

        for col in self.df.columns:
            lname = col.lower()

            if any(k in lname for k in skip_keywords):
                continue

            if pd.api.types.is_numeric_dtype(self.df[col]):
                continue

            if self.df[col].nunique(dropna=True) <= 1:
                continue

            if not (
                pd.api.types.is_object_dtype(self.df[col])
                or pd.api.types.is_string_dtype(self.df[col])
            ):
                continue

            parsed = pd.to_datetime(self.df[col], errors="coerce")
            if parsed.notna().mean() >= 0.8:
                datetime_cols.append(col)

        return datetime_cols

    # ------------------------
    # STRATEGY SELECTION
    # ------------------------

    def choose_missing_strategy(self):
        strategies = {}

        for col, pct in self.missing_report.items():
            if pct == 0:
                strategies[col] = "none"
            elif pct > self.config["missing_threshold"]:
                strategies[col] = "drop"
            elif col in self.meta["numerical"]:
                strategies[col] = "median"
            elif col in self.meta["categorical"]:
                strategies[col] = "mode"
            elif col in self.meta["datetime"]:
                strategies[col] = "interpolate"
            else:
                strategies[col] = "mode"

        return strategies

    def choose_outlier_strategy(self):
        strategies = {}

        for col, count in self.outlier_report.items():
            if count == 0:
                strategies[col] = "none"
            elif count < 5:
                strategies[col] = "winsorize"
            else:
                strategies[col] = "remove"

        return strategies

    # ------------------------
    # PIPELINE
    # ------------------------

    def run(self, verbose=None):
        if verbose is None:
            verbose = self.verbose

        if verbose:
            print("\n===== AutoClean Started =====")

        before_df = self.df.copy()
    
        self.df.columns = (
        self.df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
)

        # 1. ANALYSIS
        self.analyze_missing()
        self.analyze_dtypes()
        self.analyze_outliers()

        if verbose:
            print("Detected Metadata:", self.analysis["dtypes"])

        # 2. BASIC CLEANING
        self.df = standardize_column_names(self.df)
        self.df = remove_duplicates(self.df)
        self.df = drop_empty_columns(self.df)

        # 3. MISSING VALUES
        before_na = self.df.isna().sum().sum()
        self.df = handle_missing(self.df)
        after_na = self.df.isna().sum().sum()
        self.metrics["missing_fixed"] += int(before_na - after_na)

        # 4. OUTLIERS
        self.df, removed = remove_outliers(
            self.df,
            factor=self.config["iqr_factor"]
        )
        self.metrics["outliers_removed"] += removed

        # 5. CONSTANT COLUMNS
        constants = detect_constant_columns(self.df)
        self.metrics["columns_dropped"] += len(constants)
        self.df.drop(columns=constants, inplace=True)

        # 6. REPORT
        generate_report(
            before_df=before_df,
            after_df=self.df,
            missing_fixed=self.metrics["missing_fixed"],
            outliers_removed=self.metrics["outliers_removed"],
        )

        if verbose:
            print("===== AutoClean Completed =====\n")

        return self.df

    # ------------------------
    # DEBUG SUMMARY
    # ------------------------

    def summary(self):
        print("===== AutoClean Analysis Summary =====")
        print("\nMissing %:")
        for k, v in self.analysis.get("missing", {}).items():
            print(f"  {k}: {v:.2%}")
        print("\nDtypes:")
        print(self.analysis.get("dtypes", {}))
        print("\nOutliers:")
        print(self.analysis.get("outliers", {}))
        print("======================================")
