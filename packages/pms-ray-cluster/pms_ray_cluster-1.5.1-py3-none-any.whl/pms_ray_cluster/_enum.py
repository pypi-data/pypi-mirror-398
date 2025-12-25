from ._dependency import *


class AcceleratorType(Enum):
    nvidia_rtx_2080_ti = auto()
    nvidia_rtx_3090 = auto()
    nvidia_rtx_4090 = auto()
    furiosa_warboy = auto()
    nvidia_a10g = auto()


class ClusterType(Enum):
    onpremise_4by4 = auto()
    aws_us_west_2_dev = auto()
    aws_us_west_2_prod = auto()
