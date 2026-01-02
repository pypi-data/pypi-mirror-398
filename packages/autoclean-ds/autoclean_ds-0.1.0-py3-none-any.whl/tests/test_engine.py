import pandas as pd
from autoclean.engine import AutoClean

def test_metadata_detection():
    df = pd.DataFrame({
        "age": [20, 30],
        "name": ["A", "B"],
        "join_date": ["2023-01-01", "2023-01-02"]
    })

    ac = AutoClean(df)
    meta = ac.analyze()

    assert "numerical" in meta
    assert "categorical" in meta
    assert "datetime" in meta


def test_choose_missing_strategy():
    df = pd.DataFrame({
        "age": [20, None],
        "name": ["A", None]
    })

    ac = AutoClean(df)
    strategy = ac.choose_missing_strategy()

    assert strategy in ("mean", "median", "mode")


def test_pipeline_runs_end_to_end():
    df = pd.DataFrame({
        "Name": ["A", "B", None],
        "AGE": [10, None, 30],
        "JoinDate": ["2024-01-01", None, "2024-01-03"]
    })

    ac = AutoClean(df)
    cleaned = ac.run()

    assert cleaned is not None
    assert cleaned.shape[0] > 0
