#!/usr/bin/env python
"""
Optuna Pruner 직렬화/역직렬화 테스트

모든 Optuna Pruner가 올바르게 직렬화되고 복원되는지 검증합니다.
특히 PatientPruner의 wrapped_pruner 재귀 처리를 중점적으로 테스트합니다.
"""

import sys
import os
import json
import optuna
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../runners'))

from aiauto.serializer import object_to_json
from runner_create_study import from_json, PRUNER_WHITELIST


def test_nop_pruner():
    """NopPruner 테스트 - 파라미터 없음"""
    pruner = optuna.pruners.NopPruner()
    json_str = object_to_json(pruner)
    
    # JSON 파싱 가능 여부 확인
    parsed = json.loads(json_str)
    assert parsed["cls"] == "NopPruner"
    # NopPruner는 파라미터가 없으므로 args가 비어있거나 없을 수 있음
    
    # 역직렬화
    restored = from_json(json_str, PRUNER_WHITELIST)
    assert type(restored).__name__ == "NopPruner"


def test_median_pruner():
    """MedianPruner 테스트 - 기본 파라미터"""
    pruner = optuna.pruners.MedianPruner(
        n_startup_trials=5,
        n_warmup_steps=10,
        interval_steps=2
    )
    json_str = object_to_json(pruner)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "MedianPruner"
    assert parsed["kwargs"]["n_startup_trials"] == 5
    assert parsed["kwargs"]["n_warmup_steps"] == 10
    assert parsed["kwargs"]["interval_steps"] == 2
    
    restored = from_json(json_str, PRUNER_WHITELIST)
    assert type(restored).__name__ == "MedianPruner"
    assert restored._n_startup_trials == 5
    assert restored._n_warmup_steps == 10
    assert restored._interval_steps == 2


def test_percentile_pruner():
    """PercentilePruner 테스트 - percentile 필수 파라미터"""
    pruner = optuna.pruners.PercentilePruner(
        percentile=25.0,
        n_startup_trials=3
    )
    json_str = object_to_json(pruner)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "PercentilePruner"
    assert parsed["kwargs"]["percentile"] == 25.0
    assert parsed["kwargs"]["n_startup_trials"] == 3
    
    restored = from_json(json_str, PRUNER_WHITELIST)
    assert type(restored).__name__ == "PercentilePruner"
    assert restored._percentile == 25.0


def test_patient_pruner_with_wrapped():
    """PatientPruner 테스트 - wrapped_pruner 재귀 처리"""
    wrapped = optuna.pruners.MedianPruner(n_startup_trials=10)
    pruner = optuna.pruners.PatientPruner(
        wrapped_pruner=wrapped,
        patience=3,
        min_delta=0.1
    )
    json_str = object_to_json(pruner)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "PatientPruner"
    assert parsed["kwargs"]["patience"] == 3
    assert parsed["kwargs"]["min_delta"] == 0.1
    
    # wrapped_pruner가 재귀적으로 직렬화되었는지 확인
    assert "wrapped_pruner" in parsed["kwargs"]
    assert parsed["kwargs"]["wrapped_pruner"]["cls"] == "MedianPruner"
    assert parsed["kwargs"]["wrapped_pruner"]["kwargs"]["n_startup_trials"] == 10
    
    restored = from_json(json_str, PRUNER_WHITELIST)
    assert type(restored).__name__ == "PatientPruner"
    assert restored._patience == 3
    assert restored._min_delta == 0.1
    assert type(restored._wrapped_pruner).__name__ == "MedianPruner"
    assert restored._wrapped_pruner._n_startup_trials == 10


def test_patient_pruner_without_wrapped():
    """PatientPruner 테스트 - wrapped_pruner None으로"""
    pruner = optuna.pruners.PatientPruner(wrapped_pruner=None, patience=5)
    json_str = object_to_json(pruner)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "PatientPruner"
    assert parsed["kwargs"]["patience"] == 5
    # wrapped_pruner가 None이면 직렬화에서 제외될 수 있음
    if "wrapped_pruner" in parsed["kwargs"]:
        assert parsed["kwargs"]["wrapped_pruner"] is None
    
    restored = from_json(json_str, PRUNER_WHITELIST)
    assert type(restored).__name__ == "PatientPruner"
    assert restored._patience == 5
    assert restored._wrapped_pruner is None


def test_threshold_pruner():
    """ThresholdPruner 테스트"""
    pruner = optuna.pruners.ThresholdPruner(
        lower=0.1,
        upper=0.9,
        n_warmup_steps=5
    )
    json_str = object_to_json(pruner)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "ThresholdPruner"
    assert parsed["kwargs"]["lower"] == 0.1
    assert parsed["kwargs"]["upper"] == 0.9
    
    restored = from_json(json_str, PRUNER_WHITELIST)
    assert type(restored).__name__ == "ThresholdPruner"
    assert restored._lower == 0.1
    assert restored._upper == 0.9


def test_successive_halving_pruner():
    """SuccessiveHalvingPruner 테스트"""
    pruner = optuna.pruners.SuccessiveHalvingPruner(
        min_resource=1,
        reduction_factor=4,
        min_early_stopping_rate=0
    )
    json_str = object_to_json(pruner)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "SuccessiveHalvingPruner"
    
    restored = from_json(json_str, PRUNER_WHITELIST)
    assert type(restored).__name__ == "SuccessiveHalvingPruner"


def test_hyperband_pruner():
    """HyperbandPruner 테스트"""
    pruner = optuna.pruners.HyperbandPruner(
        min_resource=1,
        max_resource=100,
        reduction_factor=3
    )
    json_str = object_to_json(pruner)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "HyperbandPruner"
    assert parsed["kwargs"]["min_resource"] == 1
    assert parsed["kwargs"]["max_resource"] == 100
    assert parsed["kwargs"]["reduction_factor"] == 3
    
    restored = from_json(json_str, PRUNER_WHITELIST)
    assert type(restored).__name__ == "HyperbandPruner"


if __name__ == "__main__":
    # 각 테스트 실행
    test_nop_pruner()
    print("✅ NopPruner test passed")
    
    test_median_pruner()
    print("✅ MedianPruner test passed")
    
    test_percentile_pruner()
    print("✅ PercentilePruner test passed")
    
    test_patient_pruner_with_wrapped()
    print("✅ PatientPruner with wrapped test passed")
    
    test_patient_pruner_without_wrapped()
    print("✅ PatientPruner without wrapped test passed")
    
    test_threshold_pruner()
    print("✅ ThresholdPruner test passed")
    
    test_successive_halving_pruner()
    print("✅ SuccessiveHalvingPruner test passed")
    
    test_hyperband_pruner()
    print("✅ HyperbandPruner test passed")
    
    print("\n✅ All Pruner tests passed!")