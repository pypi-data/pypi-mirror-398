from importlib import resources
import pandas as pd

def data() -> pd.DataFrame:
    """
    Load the bundled example dataset shipped with sunlm.
    """
    with resources.as_file(resources.files("sunlm._data").joinpath("test_data.xlsx")) as p:
        return pd.read_excel(p)