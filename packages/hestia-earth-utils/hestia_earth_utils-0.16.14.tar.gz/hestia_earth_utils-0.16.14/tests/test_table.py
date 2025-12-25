import pandas as pd

from .utils import fixtures_path
from hestia_earth.utils.table import format_for_upload


def test_format_for_upload():
    filepath = f"{fixtures_path}/table/format/sample.csv"
    expected = pd.read_csv(f"{fixtures_path}/table/format/output.csv", index_col=None)
    df = format_for_upload(filepath)
    assert df.to_string() == expected.to_string()
