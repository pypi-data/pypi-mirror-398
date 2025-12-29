import pandas as pd
from importlib import resources


def _load_data():
    """
    Load the bundled example dataset shipped with sunlm.
    """
    with resources.files("sunlm.data").joinpath("test_data.xlsx").open("rb") as f:
        return pd.read_excel(f)


# 핵심: data라는 이름을 함수에 바인딩
data = _load_data