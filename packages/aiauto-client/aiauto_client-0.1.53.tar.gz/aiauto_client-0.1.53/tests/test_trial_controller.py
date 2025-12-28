#!/usr/bin/env python
"""
TrialController Singleton Pattern Tests

Verifies that TrialController implements singleton pattern correctly:
1. Same trial returns same instance
2. Logs accumulate across multiple instantiations
3. Different trials get different instances
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import optuna
from aiauto import TrialController


@pytest.fixture(autouse=True)
def clear_singleton_instances():
    """Clear TrialController singleton instances between tests"""
    yield
    TrialController._instances.clear()


def test_singleton_same_trial():
    """Test that same trial returns same TrialController instance"""
    storage = optuna.storages.InMemoryStorage()
    study = optuna.create_study(storage=storage, study_name='test-singleton')
    trial = study.ask()

    tc1 = TrialController(trial)
    tc2 = TrialController(trial)

    # Same trial should return same instance
    assert tc1 is tc2, "Same trial should return same TrialController instance"
    assert id(tc1) == id(tc2), "Instance IDs should match"
    assert tc1.logs is tc2.logs, "Logs list should be shared"

    study.tell(trial, 1.0)


def test_log_accumulation():
    """Test that logs accumulate across multiple instantiations"""
    storage = optuna.storages.InMemoryStorage()
    study = optuna.create_study(storage=storage, study_name='test-accumulation')
    trial = study.ask()

    tc1 = TrialController(trial)
    tc1.log("Log from tc1")

    tc2 = TrialController(trial)
    tc2.log("Log from tc2")

    # Both should see accumulated logs
    assert len(tc1.logs) == 2, "tc1 should see both logs"
    assert len(tc2.logs) == 2, "tc2 should see both logs"
    assert tc1.logs == ["Log from tc1", "Log from tc2"], "Logs should match"
    assert tc1.log_count == 2, "Log count should be 2"
    assert tc2.log_count == 2, "Log count should be 2"

    study.tell(trial, 1.0)


def test_different_trials_different_instances():
    """Test that different trials get different TrialController instances"""
    storage = optuna.storages.InMemoryStorage()
    study = optuna.create_study(storage=storage, study_name='test-different-trials')

    trial1 = study.ask()
    trial1_id = getattr(trial1, '_trial_id', id(trial1))
    tc1 = TrialController(trial1)
    tc1.log("Trial 1 log")
    study.tell(trial1, 1.0)

    trial2 = study.ask()
    trial2_id = getattr(trial2, '_trial_id', id(trial2))
    tc2 = TrialController(trial2)
    tc2.log("Trial 2 log")

    # Different trials should have different instances
    assert tc1 is not tc2, "Different trials should have different instances"
    assert trial1_id != trial2_id, "Trial IDs should be different"
    assert len(tc1.logs) == 1, f"tc1 should have 1 log, got {len(tc1.logs)}: {tc1.logs}"
    assert len(tc2.logs) == 1, f"tc2 should have 1 log, got {len(tc2.logs)}: {tc2.logs}"
    assert tc1.logs[0] == "Trial 1 log"
    assert tc2.logs[0] == "Trial 2 log"

    study.tell(trial2, 2.0)


def test_singleton_with_frozen_trial():
    """Test singleton works with FrozenTrial (used in callbacks)"""
    storage = optuna.storages.InMemoryStorage()
    study = optuna.create_study(storage=storage, study_name='test-frozen')

    # Create trial and log something
    trial = study.ask()
    tc1 = TrialController(trial)
    tc1.log("Log from active trial")
    study.tell(trial, 1.0)

    # Get frozen trial
    frozen_trial = study.trials[0]
    tc2 = TrialController(frozen_trial)

    # Should be same instance if trial_id matches
    # Note: This tests if singleton key (_trial_id) works across Trial/FrozenTrial
    assert tc1.logs == tc2.logs, "Logs should be accessible from frozen trial"


def test_runner_scenario():
    """
    Simulate the runner_trial.py scenario:
    - Runner creates tc and calls flush() in finally block
    - User's objective creates another tc and logs
    - Runner's flush should flush user's logs too (singleton pattern)
    """
    storage = optuna.storages.InMemoryStorage()
    study = optuna.create_study(storage=storage, study_name='test-runner-scenario')

    trial = study.ask()

    # Simulate runner_trial.py
    runner_tc = TrialController(trial)

    try:
        # Simulate user's objective function
        def objective(trial):
            user_tc = TrialController(trial)
            user_tc.log("User log 1")
            user_tc.log("User log 2")
            # User doesn't call flush()
            return 1.0

        result = objective(trial)
    finally:
        # Runner calls flush
        runner_tc.flush()

    # After runner's flush, all logs should be saved
    # (we can't test _save_note directly without optuna_dashboard,
    #  but we can verify singleton worked)
    assert len(runner_tc.logs) == 2, f"Runner should see user's logs via singleton, got {len(runner_tc.logs)}: {runner_tc.logs}"
    assert runner_tc.logs == ["User log 1", "User log 2"]

    study.tell(trial, result)


def test_set_user_attr_reserved_keys():
    """Test that setting reserved keys raises ValueError"""
    storage = optuna.storages.InMemoryStorage()
    study = optuna.create_study(storage=storage, study_name='test-reserved-keys')
    trial = study.ask()

    tc = TrialController(trial)

    # All reserved keys should raise ValueError
    reserved_keys = ['pod_name', 'trialbatch_name', 'gpu_name', 'artifact_id', 'artifact_removed']

    for key in reserved_keys:
        with pytest.raises(ValueError, match=f"Cannot set user_attr '{key}': This key is reserved by the system"):
            tc.set_user_attr(key, 'test_value')

    study.tell(trial, 1.0)


def test_set_user_attr_custom_keys_success():
    """Test that setting custom (non-reserved) keys works normally"""
    storage = optuna.storages.InMemoryStorage()
    study = optuna.create_study(storage=storage, study_name='test-custom-keys')
    trial = study.ask()

    tc = TrialController(trial)

    # Custom keys should work normally
    tc.set_user_attr('my_metric', 0.95)
    tc.set_user_attr('custom_data', {'key': 'value'})
    tc.set_user_attr('iteration', 42)

    # Verify attributes were set correctly
    assert trial.user_attrs['my_metric'] == 0.95
    assert trial.user_attrs['custom_data'] == {'key': 'value'}
    assert trial.user_attrs['iteration'] == 42

    study.tell(trial, 1.0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
