from io import BytesIO
import pandas as pd
import pyarrow as pa
from xtgeo import surface_from_file, gridproperty_from_file

from pathlib import Path
from fmu.dataio import ExportData
from fmu.dataio._utils import export_file, object_to_bytes


PATH = Path(".").cwd() / "../data/drogon/ertrun1/realization-0/iter-0/share/results"
print(PATH)


def test_to_bytes():
    print(PATH.exists())
    func = None
    for file in PATH.glob("**/[!.]*.*"):
        if file.suffix == ".gri":
            func = surface_from_file
            obj = func(file)
        elif file.suffix == ".roff":
            func = gridproperty_from_file
            obj = func(file)
        elif file.suffix == ".csv":
            func = pd.read_csv
            obj = func(file)
        elif file.suffix == ".arrow":
            func = pa.feather.read_table
            obj = func(file)
        else:
            print(f"Not reading this {file}")

        stream = object_to_bytes(obj)
        assert isinstance(stream, BytesIO), "right type for {type(obj)}"
        # exported_obj = func(stream)
