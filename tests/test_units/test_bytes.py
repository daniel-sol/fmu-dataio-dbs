import os
from io import BytesIO
import numpy as np
import pandas as pd
import pyarrow as pa
from xtgeo import surface_from_file, gridproperty_from_file
from pathlib import Path
from fmu.dataio import ExportData
from fmu.dataio._utils import object_to_bytes, upload_to_sumo
from fmu.sumo.uploader import CaseOnDisk, SumoConnection
from fmu.config.utilities import yaml_load
import pytest
import yaml

FMU_RUN = Path(__file__).parent / "../data/drogon/ertrun1/"
RESULTS = FMU_RUN / "realization-0/iter-0/share/results"
CASE_META = FMU_RUN / "share/metadata/fmu_case.yml"


@pytest.fixture(name="sumouuid", scope="session")
def fixture_case():
    """Return case uuid

    Args:
        case_metadata_path (str): path to metadatafile
        sumo_conn (SumoConnection): Connection to given sumo environment

    Returns:
        str: case uuid
    """
    sumo_conn = SumoConnection(env="test")
    case = CaseOnDisk(
        case_metadata_path=CASE_META,
        sumo_connection=sumo_conn,
        verbosity="DEBUG",
    )
    # Register the case in Sumo
    sumo_uuid = case.register()
    return sumo_uuid


def test_object_to_bytes():
    """Test the function object_to_bytes"""
    func = None
    flag = None
    for file_path in RESULTS.glob("**/[!.]*.csv"):
        print(file_path)
        if file_path.suffix == ".gri":
            func = surface_from_file
            obj = func(file_path)
        elif file_path.suffix == ".roff":
            func = gridproperty_from_file
            obj = func(file_path)
        elif file_path.suffix == ".csv":
            func = pd.read_csv
            flag = True
            obj = func(file_path)
        elif file_path.suffix == ".arrow":
            func = pa.feather.read_table
            obj = func(file_path)
        else:
            print(f"Not reading this {file_path}")

        stream = object_to_bytes(obj, flag)
        assert isinstance(stream, BytesIO), "right type for {type(obj)}"
        new_obj = func(stream)
        ass_mess = f"{file_path} does not come up as identical {obj} vs {new_obj}"
        try:
            assert obj == new_obj, ass_mess
        except ValueError:
            # rounding done because it is not possible to exactly reproduce the data
            # this should be fine
            assert obj.round(1).compare(new_obj.round(1)).empty, ass_mess


def test_failing_object_to_bytes():
    """Test that object that is not defined within export doesn't trip over"""
    obj = np.random.normal(0, 1, 50)
    stream = object_to_bytes(obj)
    assert stream is None, f"this should return None, but returns {obj}"


def test_upload(sumouuid):
    print(sumouuid)
    os.chdir(FMU_RUN / "realization-0/iter-0")
    config = yaml_load(FMU_RUN / "../global_config2/global_variables.yml")
    exp = ExportData(config=config, name="banana")
    obj = pd.DataFrame({"tut": [1, 2, 3]})
    meta = exp.generate_metadata(obj)
    print(meta)
    with open("meta.yml", "w") as out:
        yaml.dump(meta, out)
    upload_to_sumo("test", sumouuid, meta, object_to_bytes(obj))
