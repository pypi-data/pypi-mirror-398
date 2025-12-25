from ._dependency import *
from ._enum import *

PROJECT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
CONFIG_ASSET_DIR = os.path.join(PROJECT_DIR, "asset")

CONFIG_PATH_MAP: Dict[str, str] = {
    "temp": os.path.join(CONFIG_ASSET_DIR, "cluster_config.yml"),
    "dev": os.path.join(CONFIG_ASSET_DIR, "dev.cluster_config.yml"),
    "prod": os.path.join(CONFIG_ASSET_DIR, "prod.cluster_config.yml"),
}
MIN_CLIENT_PORT = 5000
DEFAULT_CLIENT_PORT = 10001
DEFAULT_NAME_SPACE = "default_namespace"

CLUSTER_ACCELERATOR_MAP: Dict[ClusterType, List[AcceleratorType]] = {
    ClusterType.onpremise_4by4: [
        AcceleratorType.nvidia_rtx_2080_ti,
        AcceleratorType.nvidia_rtx_4090,
        AcceleratorType.furiosa_warboy,
    ],
    ClusterType.aws_us_west_2_dev: [
        AcceleratorType.nvidia_a10g,
    ],
    ClusterType.aws_us_west_2_prod: [
        AcceleratorType.nvidia_a10g,
    ],
}
