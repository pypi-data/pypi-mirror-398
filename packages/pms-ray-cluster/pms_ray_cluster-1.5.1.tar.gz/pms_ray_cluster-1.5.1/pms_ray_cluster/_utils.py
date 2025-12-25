from typing import List
from ._enum import AcceleratorType
from ._dependency import *
from ._const import *


def _cli(command: str) -> Tuple[int, str]:
    proc = subprocess.run([command], shell=True, stdout=subprocess.PIPE)
    returncode = proc.returncode
    std_out = proc.stdout.decode("utf-8")
    logger.info(f"_cli | {command} | {returncode:03d} | {std_out}")
    return returncode, std_out


def get_head_ip(config_path: str) -> Union[str, None]:
    assert os.path.exists(config_path)
    assert os.path.isfile(config_path)
    return_code, out = _cli(f"ray get-head-ip {config_path}")
    if return_code != 0:
        return None
    ips = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", str(out))
    assert len(ips) == 1
    return ips[0]


def get_path_from_type(config_type: str):
    try:
        logger.info(f"Try to convert '{config_type}' to config_path.")
        return CONFIG_PATH_MAP[config_type]
    except Exception as ex:
        logger.error(
            f"ERROR!, {ex}.\nSelect the config type from {[k for k in CONFIG_PATH_MAP]}"
        )
        return None


def get_accelerators_from_cluster(cluster_type: ClusterType) -> List[AcceleratorType]:
    return CLUSTER_ACCELERATOR_MAP[cluster_type]


def is_accelerator_in_cluster(
    cluster_Type: ClusterType, accelerator_type: AcceleratorType
) -> bool:
    return accelerator_type in CLUSTER_ACCELERATOR_MAP[cluster_Type]


def is_valid_ipv4(ip):
    pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    if re.match(pattern, ip):
        return True
    else:
        return False
