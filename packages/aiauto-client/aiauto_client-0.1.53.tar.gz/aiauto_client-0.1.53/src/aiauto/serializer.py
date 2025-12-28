import inspect
import json
from typing import Callable, Union, List, Optional


def serialize(objective: Callable) -> str:
    try:
        return inspect.getsource(objective)
    except (OSError, TypeError) as e:
        raise ValueError(
            "Serialize 실패 objective 함수는 파일로 저장되어야 합니다\n"
            "REPL/Jupyter Notebook에서는 %%writefile magic을 사용해서 local 에 file 로 저장하세요\n\n"
            "%%writefile objective.py\n"
            "def objective(trial):\n"
            "    # 함수 내용\n"
            "    ...\n\n"
            "그 다음:\n"
            "from objective import objective\n"
            "study.optimize(objective, ...)"
        ) from e


def build_requirements(file_path: Optional[str] = None, reqs: Optional[List[str]] = None) -> str:
    if file_path and reqs:
        raise ValueError("requirements_file과 requirements_list는 동시에 지정할 수 없습니다")

    if file_path:
        with open(file_path, 'r') as f:
            return f.read()
    elif reqs:
        return "\n".join(reqs)
    else:
        return ""


def object_to_json(obj: Union[object, dict, None]) -> str:
    if obj is None:
        return ""

    if isinstance(obj, dict):
        return json.dumps(obj)

    cls = type(obj)
    module_name = cls.__module__
    class_name = cls.__name__

    if not module_name.startswith('optuna.'):
        raise ValueError(f"optuna 코어 클래스만 지원합니다: {class_name}")

    # __init__의 실제 파라미터만 가져오기  
    sig = inspect.signature(cls.__init__)
    valid_params = set(sig.parameters.keys()) - {'self'}
    
    # Optuna 객체들은 __dict__에 _param_name 형태로 저장
    kwargs = {}
    for key, value in obj.__dict__.items():
        if key.startswith('_'):
            param_name = key[1:]  # _ 제거
            
            # __init__의 실제 파라미터인지 확인
            if param_name in valid_params:
                # PatientPruner의 wrapped_pruner 특별 처리
                if class_name == "PatientPruner" and param_name == "wrapped_pruner" and value is not None:
                    kwargs[param_name] = json.loads(object_to_json(value))
                # CmaEsSampler와 QMCSampler의 independent_sampler 특별 처리
                elif param_name == "independent_sampler" and value is not None and class_name in ["CmaEsSampler", "QMCSampler"]:
                    kwargs[param_name] = json.loads(object_to_json(value))
                # Callable 타입은 제외 (gamma, weights 등)
                elif not callable(value):
                    kwargs[param_name] = value

    return json.dumps({
        "cls": class_name,
        "kwargs": kwargs
    })
