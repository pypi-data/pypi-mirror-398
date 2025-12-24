import pandas as pd
import pytest
from pandas_cobol_io import RowLengthNotSameError


def test_to_fwf():
    expected = "10111ﾃｽﾄﾊﾞﾝｸ        022ﾃｽﾄｼﾃﾝ         11234567ｶ)ﾃｽﾄｼｮｳｼﾞ                    0000008000\n"
    info = {
        "data_division": ("9", 1),
        "bank_cd": ("9", 4),
        "bank_name": ("X", 15),
        "branch_cd": ("9", 3),
        "branch_name": ("X", 15),
        "kind_of_account": ("9", 1),
        "account_cd": ("9", 7),
        "name": ("X", 30),
        "amount": ("9", 10),
    }
    args = {
        "io": "tests/bin/dummy_balance_list.xlsx",
        "header": None,
    }
    # success
    df = pd.read_excel(sheet_name="success", **args)
    df = df.rename(columns={i: x for i, x in enumerate(info.keys())})
    assert df.to_fwf(info.values(), "ansi")[0] == expected
    # failure
    with pytest.raises(RowLengthNotSameError):
        df = pd.read_excel(sheet_name="failure", **args)
        df = df.rename(columns={i: x for i, x in enumerate(info.keys())})
        df.to_fwf(info.values(), "ansi")


def test_parse_fwf():
    expected_df = pd.read_pickle("tests/bin/expected_df.pkl")
    params = {
        "ID": 5,
        "NAME": 10,
    }
    # success
    df = pd.parse_fwf("tests/bin/dummy_fwf.txt", params, enc="utf-8")["df"]
    assert df.equals(expected_df)
    # failure
    with pytest.raises(UnicodeDecodeError):
        pd.parse_fwf("tests/bin/dummy_fwf.txt", params, enc="ansi")["df"]
