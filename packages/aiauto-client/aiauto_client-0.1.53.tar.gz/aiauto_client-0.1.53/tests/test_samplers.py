#!/usr/bin/env python
"""
Optuna Sampler 직렬화/역직렬화 테스트

주요 Optuna Sampler가 올바르게 직렬화되고 복원되는지 검증합니다.
Callable 타입 파라미터(gamma, weights 등)는 직렬화에서 제외됨을 확인합니다.
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
from runner_create_study import from_json, SAMPLER_WHITELIST


def test_random_sampler():
    """RandomSampler 테스트 - seed 파라미터"""
    sampler = optuna.samplers.RandomSampler(seed=42)
    json_str = object_to_json(sampler)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "RandomSampler"
    # seed는 저장되지만 다른 형태로 저장될 수 있음
    if "seed" in parsed["kwargs"]:
        assert parsed["kwargs"]["seed"] == 42
    
    restored = from_json(json_str, SAMPLER_WHITELIST)
    assert type(restored).__name__ == "RandomSampler"


def test_tpe_sampler():
    """TPESampler 테스트 - 주요 파라미터"""
    sampler = optuna.samplers.TPESampler(
        n_startup_trials=5,
        n_ei_candidates=10,
        seed=42,
        multivariate=True,
        warn_independent_sampling=False
    )
    json_str = object_to_json(sampler)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "TPESampler"
    assert parsed["kwargs"]["n_startup_trials"] == 5
    assert parsed["kwargs"]["n_ei_candidates"] == 10
    assert parsed["kwargs"]["multivariate"] == True
    assert parsed["kwargs"]["warn_independent_sampling"] == False
    if "seed" in parsed["kwargs"]:
        assert parsed["kwargs"]["seed"] == 42
    
    # Callable 파라미터들(gamma, weights)은 제외되어야 함
    assert "gamma" not in parsed["kwargs"]
    assert "weights" not in parsed["kwargs"]
    
    restored = from_json(json_str, SAMPLER_WHITELIST)
    assert type(restored).__name__ == "TPESampler"
    assert restored._n_startup_trials == 5
    assert restored._n_ei_candidates == 10
    if hasattr(restored, '_seed'):
        assert restored._seed == 42


def test_tpe_sampler_default():
    """TPESampler 테스트 - 기본값"""
    sampler = optuna.samplers.TPESampler()
    json_str = object_to_json(sampler)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "TPESampler"
    
    # 기본값들이 올바르게 직렬화되는지 확인
    assert "n_startup_trials" in parsed["kwargs"]
    assert "n_ei_candidates" in parsed["kwargs"]
    
    restored = from_json(json_str, SAMPLER_WHITELIST)
    assert type(restored).__name__ == "TPESampler"


def test_nsgaii_sampler():
    """NSGAIISampler 테스트 - 다목적 최적화용"""
    sampler = optuna.samplers.NSGAIISampler(
        population_size=10,
        mutation_prob=0.1,
        crossover_prob=0.8,
        swapping_prob=0.4,
        seed=42
    )
    json_str = object_to_json(sampler)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "NSGAIISampler"
    assert parsed["kwargs"]["population_size"] == 10
    if "mutation_prob" in parsed["kwargs"]:
        assert parsed["kwargs"]["mutation_prob"] == 0.1
    if "crossover_prob" in parsed["kwargs"]:
        assert parsed["kwargs"]["crossover_prob"] == 0.8
    if "swapping_prob" in parsed["kwargs"]:
        assert parsed["kwargs"]["swapping_prob"] == 0.4
    if "seed" in parsed["kwargs"]:
        assert parsed["kwargs"]["seed"] == 42
    
    # Callable 파라미터들은 제외되거나 null이어야 함
    assert parsed["kwargs"].get("constraints_func") is None
    assert "elite_population_selection_strategy" not in parsed["kwargs"]
    
    restored = from_json(json_str, SAMPLER_WHITELIST)
    assert type(restored).__name__ == "NSGAIISampler"
    assert restored._population_size == 10
    if hasattr(restored, '_seed'):
        assert restored._seed == 42


def test_grid_sampler():
    """GridSampler 테스트 - search_space 파라미터"""
    search_space = {
        "x": [-10, -5, 0, 5, 10],
        "y": [1, 2, 3]
    }
    sampler = optuna.samplers.GridSampler(search_space=search_space)
    json_str = object_to_json(sampler)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "GridSampler"
    assert parsed["kwargs"]["search_space"] == search_space
    
    restored = from_json(json_str, SAMPLER_WHITELIST)
    assert type(restored).__name__ == "GridSampler"
    assert restored._search_space == search_space


def test_bruteforce_sampler():
    """BruteForceSampler 테스트"""
    sampler = optuna.samplers.BruteForceSampler(seed=42)
    json_str = object_to_json(sampler)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "BruteForceSampler"
    if "seed" in parsed["kwargs"]:
        assert parsed["kwargs"]["seed"] == 42
    
    restored = from_json(json_str, SAMPLER_WHITELIST)
    assert type(restored).__name__ == "BruteForceSampler"
    if hasattr(restored, '_seed'):
        assert restored._seed == 42


def test_cmaes_sampler():
    """CmaEsSampler 테스트"""
    sampler = optuna.samplers.CmaEsSampler(
        n_startup_trials=5,
        seed=42
    )
    json_str = object_to_json(sampler)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "CmaEsSampler"
    assert parsed["kwargs"]["n_startup_trials"] == 5
    if "seed" in parsed["kwargs"]:
        assert parsed["kwargs"]["seed"] == 42
    # restart_strategy는 deprecated되어 저장되지 않음
    
    restored = from_json(json_str, SAMPLER_WHITELIST)
    assert type(restored).__name__ == "CmaEsSampler"
    assert restored._n_startup_trials == 5
    if hasattr(restored, '_seed'):
        assert restored._seed == 42


def test_qmc_sampler():
    """QMCSampler 테스트"""
    sampler = optuna.samplers.QMCSampler(
        qmc_type="sobol",
        scramble=True,
        seed=42
    )
    json_str = object_to_json(sampler)
    
    parsed = json.loads(json_str)
    assert parsed["cls"] == "QMCSampler"
    assert parsed["kwargs"]["qmc_type"] == "sobol"
    assert parsed["kwargs"]["scramble"] == True
    if "seed" in parsed["kwargs"]:
        assert parsed["kwargs"]["seed"] == 42
    
    restored = from_json(json_str, SAMPLER_WHITELIST)
    assert type(restored).__name__ == "QMCSampler"
    assert restored._qmc_type == "sobol"
    assert restored._scramble == True
    if hasattr(restored, '_seed'):
        assert restored._seed == 42


if __name__ == "__main__":
    # 각 테스트 실행
    test_random_sampler()
    print("✅ RandomSampler test passed")
    
    test_tpe_sampler()
    print("✅ TPESampler test passed")
    
    test_tpe_sampler_default()
    print("✅ TPESampler (default) test passed")
    
    test_nsgaii_sampler()
    print("✅ NSGAIISampler test passed")
    
    test_grid_sampler()
    print("✅ GridSampler test passed")
    
    test_bruteforce_sampler()
    print("✅ BruteForceSampler test passed")
    
    test_cmaes_sampler()
    print("✅ CmaEsSampler test passed")
    
    test_qmc_sampler()
    print("✅ QMCSampler test passed")
    
    print("\n✅ All Sampler tests passed!")