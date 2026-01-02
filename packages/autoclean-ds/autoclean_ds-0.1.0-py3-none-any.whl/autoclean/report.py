class Report:
    def __init__(self):
        self.before_shape = None
        self.after_shape = None

        self.rows_removed = 0
        self.columns_dropped = 0
        self.missing_fixed = 0
        self.outliers_removed = 0

    def set_before(self, df):
        self.before_shape = df.shape

    def set_after(self, df):
        self.after_shape = df.shape

    def to_dict(self):
        return {
            "before_shape": self.before_shape,
            "after_shape": self.after_shape,
            "rows_removed": self.rows_removed,
            "columns_dropped": self.columns_dropped,
            "missing_fixed": self.missing_fixed,
            "outliers_removed": self.outliers_removed,
        }

    def show(self):
        print("\n====== AutoClean Report ======")
        print(f"Before Cleaning: {self.before_shape}")
        print(f"After Cleaning:  {self.after_shape}")
        print("\n--- Metrics ---")
        print(f"Rows Removed:     {self.rows_removed}")
        print(f"Columns Dropped:  {self.columns_dropped}")
        print(f"Missing Fixed:    {self.missing_fixed}")
        print(f"Outliers Removed: {self.outliers_removed}")
        print("==============================\n")

#Day12
import pandas as pd
import numpy as np


def memory_in_mb(df):
    """Return memory usage in MB."""
    return df.memory_usage(deep=True).sum() / 1024 / 1024


def generate_report(before_df, after_df, outliers_removed=0, missing_fixed=0):
    """
    Generate a clean Before/After cleaning report.

    Parameters
    ----------
    before_df : DataFrame
        Dataset before cleaning.

    after_df : DataFrame
        Dataset after cleaning.

    outliers_removed : int
        Number of outliers removed.

    missing_fixed : int
        Number of missing values fixed.

    Returns
    -------
    report_dict : dict
        Structured summary of what changed.
    """

    report = {}

    # -------------------------
    # 1. SHAPE CHANGES
    # -------------------------
    report["shape_before"] = before_df.shape
    report["shape_after"] = after_df.shape

    report["rows_removed"] = before_df.shape[0] - after_df.shape[0]
    report["columns_removed"] = before_df.shape[1] - after_df.shape[1]

    # -------------------------
    # 2. MISSING VALUE CHANGES
    # -------------------------
    before_missing = before_df.isna().sum().sum()
    after_missing = after_df.isna().sum().sum()

    report["missing_before"] = int(before_missing)
    report["missing_after"] = int(after_missing)
    report["missing_fixed"] = int(missing_fixed)

    # -------------------------
    # 3. OUTLIERS
    # -------------------------
    report["outliers_removed"] = int(outliers_removed)

    # -------------------------
    # 4. COLUMN CHANGES
    # -------------------------
    before_cols = set(before_df.columns)
    after_cols = set(after_df.columns)

    report["dropped_columns"] = list(before_cols - after_cols)
    report["new_columns"] = list(after_cols - before_cols)

    # -------------------------
    # 5. MEMORY USAGE
    # -------------------------
    report["memory_before_mb"] = round(memory_in_mb(before_df), 4)
    report["memory_after_mb"] = round(memory_in_mb(after_df), 4)
    report["memory_change_mb"] = round(
        report["memory_after_mb"] - report["memory_before_mb"], 4
    )

    # -------------------------
    # 6. PRINT (OPTIONAL PRETTY FORMAT)
    # -------------------------
    print("\n====== AutoClean Before/After Report ======")

    print(f"Before Cleaning: {report['shape_before']}")
    print(f"After Cleaning:  {report['shape_after']}")

    print("\n--- Column Changes ---")
    print("Dropped:", report["dropped_columns"])
    print("New:", report["new_columns"])

    print("\n--- Missing Values ---")
    print(f"Before: {report['missing_before']}")
    print(f"After:  {report['missing_after']}")
    print(f"Fixed:  {report['missing_fixed']}")

    print("\n--- Outliers ---")
    print(f"Removed: {report['outliers_removed']}")

    print("\n--- Memory Usage (MB) ---")
    print(f"Before: {report['memory_before_mb']}")
    print(f"After:  {report['memory_after_mb']}")
    print(f"Change: {report['memory_change_mb']}")

    print("===========================================")

    return report
