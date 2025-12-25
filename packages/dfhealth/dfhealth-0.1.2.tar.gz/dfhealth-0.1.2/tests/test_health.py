import pandas as pd
import pytest
import dfhealth as dh

def test_duplicate_check():
    df = pd.DataFrame({'a': [1, 2, 1], 'b': [3, 4, 3]})
    report = dh.health_check(df)
    codes = [w.code for w in report.warnings]
    assert "D001" in codes

def test_negative_check():
    df = pd.DataFrame({'age': [25, -1, 30]})
    report = dh.health_check(df)
    codes = [w.code for w in report.warnings]
    assert "N001" in codes

def test_id_like_check():
    df = pd.DataFrame({'user_id': [1, 1, 2]})
    report = dh.health_check(df)
    codes = [w.code for w in report.warnings]
    assert "I001" in codes

def test_outlier_check():
    df = pd.DataFrame({'val': [1, 2, 1, 2, 1, 2, 100]})
    report = dh.health_check(df)
    codes = [w.code for w in report.warnings]
    assert "O001" in codes

def test_date_like_check():
    df = pd.DataFrame({'date_str': ['2023-01-01', '2023-01-02', '2023-01-03']})
    report = dh.health_check(df)
    codes = [w.code for w in report.warnings]
    assert "T001" in codes
