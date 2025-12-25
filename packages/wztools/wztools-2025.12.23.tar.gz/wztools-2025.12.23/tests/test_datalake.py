import datetime as dt

from wztools.datalake import datalake
from pathlib import Path


file1 = datalake.generate_data_path(
    root_dir=Path("./data"),
    dataset_name="tv1",
    special_key="tv1",
    time_key=dt.datetime.now()
)
print(file1)
# datalake.get_data_paths()