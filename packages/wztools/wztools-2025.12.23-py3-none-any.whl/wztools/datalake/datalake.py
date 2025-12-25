import datetime as dt

from pathlib import Path
from pickletools import read_uint1
import re


def generate_data_path(
        root_dir: Path,
        dataset_name: str,
        special_key: str,
        time_key: dt.datetime,
        suffix: str="parquet"
):
    """
    根据时间点和数据集名称，生成 [suffix] 文件的标准存储路径 (包含文件名)。
    结构: ./root_dir/dataset_name/Y/M/D/YYYYMMDD_HH_[special_key].[suffix]
    Args:
        - root_dir (pathlib.Path): 数据池的根目录。
        - dataset_name (str): 数据集的名称 (e.g., 'ERA5_Hourly')。
        - time_key (datetime.datetime): 数据的时间点。
        - special_key (str): 可选的特殊标识符，如 'v2'。
    """
    # 构建目录
    partition_path = root_dir / dataset_name / \
                        f"{time_key.year}" / \
                        f"{time_key.month:02d}" / \
                        f"{time_key.day:02d}"
                        
    partition_path.mkdir(exist_ok=True, parents=True)
    # 构建文件名
    time_part = time_key.strftime("%Y%m%d_%H")
    file_stem = f"{time_part}_{special_key}"
    file_name = f"{file_stem}.{suffix}"

    return partition_path / file_name

def get_data_paths(
        root_dir: Path,
        dataset_name: str,
        special_key: str,
        start_time: dt.datetime,
        end_time: dt.datetime,
        suffix: str="parquet"
):
    """
    通过精准的时间分区索引，快速获取时间范围内的 suffix 文件路径列表。
    Args:
        - root_dir (pathlib.Path): 数据池的根目录。
        - dataset_name (str): 数据集的名称 (e.g., 'ERA5_Hourly')。
        - special_key (str): 可选的特殊标识符，如 'v2'。
        - start_time (dt.datetime): 起始时间
        - end_time (dt.datetime): 结束时间
    """
    # 初始化结果列表
    file_paths = []

    # 步骤 1: 确定需要访问的日期范围
    current_time = start_time
    delta_hour = dt.timedelta(hours=1)

    # 为了避免重复访问同一天，set 记录已处理的日期
    processed_time_points = set()

    while current_time <= end_time:
        # 步骤 2: 仅处理尚未处理的日期
        if current_time not in processed_time_points:
            partition_path = root_dir / \
                            dataset_name / \
                            f"{current_time.year}" / \
                            f"{current_time.month:02d}" / \
                            f"{current_time.day:02d}" / \
                            f"{current_time.strftime('%Y%m%d_%H')}_{special_key}.{suffix}"
            if partition_path.exists():
                file_paths.append(partition_path)
        processed_time_points.add(current_time)
        current_time += delta_hour

    if len(file_paths) == 0:
        raise ValueError("not file in paths")
    return file_paths