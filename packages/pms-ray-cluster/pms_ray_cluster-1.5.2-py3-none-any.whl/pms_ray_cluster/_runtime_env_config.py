from ._const import *


@dataclass
class DockerContainerConfig:
    """Docker 컨테이너 설정을 위한 데이터 클래스입니다.
    - image: Docker 이미지 이름과 태그입니다.
    - run_options: 컨테이너 실행 옵션의 리스트입니다.

    예:
    config = DockerContainerConfig(image="anyscale/ray-ml:latest-gpu", run_options=["--cap-add=SYS_PTRACE"])
    """

    image: str
    run_options: Optional[List[str]] = None


@dataclass
class RuntimeEnvConfig:
    """Ray 클러스터의 runtime environment를 구성하기 위한 데이터 클래스입니다.
    이 클래스를 통해 작업 디렉토리, 의존성, 환경 변수 등을 설정하여 Ray 작업 및 액터에 적용할 수 있습니다.

    Attributes:
        working_dir (Union[str, Path], optional): Ray 작업이 실행될 때 기본 작업 디렉토리로 설정됩니다.
        py_modules (List[Union[str, Path]], optional): Ray 작업에서 사용할 추가 Python 모듈의 경로 리스트입니다.
        pip (Union[List[str], str], optional): pip를 통해 설치할 패키지 목록 또는 요구 사항 파일의 경로입니다.
        conda (Union[Dict, str], optional): Conda 환경을 정의하는 사전 또는 환경 파일의 경로입니다.
        env_vars (Dict[str, str], optional): Ray 작업에 적용할 환경 변수의 사전입니다.
        container (DockerContainerConfig, optional): Docker 컨테이너 설정을 위한 DockerContainerConfig 인스턴스입니다.
        excludes (List[str], optional): 작업 디렉토리 업로드 시 제외할 파일 또는 디렉토리 목록입니다.
    """

    # 작업 디렉토리 경로입니다. Ray 작업이 실행될 때 기본 작업 디렉토리로 설정됩니다.
    # 예: "/path/to/your/project" 또는 Path 객체
    working_dir: Optional[Union[str, Path]] = None

    # 로드할 Python 모듈의 리스트입니다. 각 모듈은 디렉토리 또는 .py 파일일 수 있습니다.
    # 예: ["./my_module", "./utils"]
    py_modules: Optional[List[Union[str, Path]]] = None

    # pip를 통해 설치할 Python 패키지 목록 또는 요구 사항 파일입니다.
    # 예: ["pandas>=1.1", "ray[serve]"] 또는 "requirements.txt"
    pip: Optional[Union[List[str], str]] = None

    # Conda 환경을 정의하는 사전이나 환경 파일입니다. Ray 작업이 실행될 Conda 환경을 지정합니다.
    # 예: {"dependencies": ["numpy", "pandas"]} 또는 "environment.yml"
    conda: Optional[Union[Dict, str]] = None

    # 설정할 환경 변수의 사전입니다. 이 변수들은 Ray 작업에 의해 인식될 수 있습니다.
    # 예: {"OMP_NUM_THREADS": "1", "TF_AUTO_MIXED_PRECISION_GRAPH_REWRITE": "0"}
    env_vars: Optional[Dict[str, str]] = None

    # Docker 컨테이너 환경을 설정하는 사전입니다. 이미지 이름과 태그, 컨테이너 실행 옵션을 포함할 수 있습니다.
    # 예: {"image": "anyscale/ray-ml:latest-gpu", "run_options": ["--cap-add=SYS_PTRACE"]}
    # container: Optional[DockerContainerConfig] = None

    # 업로드 시 제외할 파일 또는 디렉토리 목록입니다. 이들은 Ray 작업 디렉토리로 업로드되지 않습니다.
    # 예: ["data", "debug_logs"]
    excludes: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """클래스 인스턴스를 `ray.init()`에 사용할 수 있는 사전 형태로 변환합니다.
        값이 None인 필드는 결과 사전에 포함되지 않습니다. DockerContainerConfig는 별도로 처리하여
        내부 구조를 사전으로 변환합니다.

        Returns:
            Dict[str, Any]: 필터링된 사전, None이 아닌 값들만 포함합니다.
        """
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if isinstance(value, DockerContainerConfig):
                    result[key] = (
                        value.__dict__
                    )  # DockerContainerConfig 인스턴스를 사전으로 변환
                else:
                    result[key] = value
        return result
