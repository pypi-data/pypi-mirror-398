"""Tests for emptyDir size parameter validation."""
import pytest
from aiauto.core import _parse_size_to_gi


class TestParseSizeToGi:
    """Test size parsing helper function."""

    def test_parse_mi_to_gi(self):
        """Test Mi to Gi conversion."""
        assert _parse_size_to_gi("500Mi") == pytest.approx(0.48828125, rel=1e-6)
        assert _parse_size_to_gi("1024Mi") == pytest.approx(1.0, rel=1e-6)
        assert _parse_size_to_gi("2048Mi") == pytest.approx(2.0, rel=1e-6)

    def test_parse_gi(self):
        """Test Gi parsing."""
        assert _parse_size_to_gi("1Gi") == 1.0
        assert _parse_size_to_gi("4Gi") == 4.0
        assert _parse_size_to_gi("0.5Gi") == 0.5

    def test_parse_empty_string(self):
        """Test empty string returns 0."""
        assert _parse_size_to_gi("") == 0.0

    def test_parse_invalid_format(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid size format"):
            _parse_size_to_gi("500")
        with pytest.raises(ValueError, match="Invalid size format"):
            _parse_size_to_gi("abc")
        with pytest.raises(ValueError, match="Invalid size format"):
            _parse_size_to_gi("500 Mi")

    def test_parse_unsupported_unit(self):
        """Test unsupported unit raises ValueError."""
        # Only Mi, Gi are allowed (binary units)
        with pytest.raises(ValueError, match="Invalid size format"):
            _parse_size_to_gi("500Ki")

    def test_parse_rejects_si_units(self):
        """Test SI units (M, G) are rejected."""
        with pytest.raises(ValueError, match="Only binary units.*are allowed"):
            _parse_size_to_gi("1G")
        with pytest.raises(ValueError, match="Only binary units.*are allowed"):
            _parse_size_to_gi("1000M")

    def test_parse_exceeds_max(self):
        """Test exceeding max limit raises ValueError."""
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("15Gi", max_gi=10.0)
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("200Gi", max_gi=100.0)

    def test_parse_within_max(self):
        """Test within max limit passes."""
        assert _parse_size_to_gi("5Gi", max_gi=10.0) == 5.0
        assert _parse_size_to_gi("50Gi", max_gi=100.0) == 50.0


class TestSharedCacheSizeValidation:
    """Test shared_cache_size parameter validation (default: 500Mi, max: 4Gi)."""

    def test_default_value_parse(self):
        """Test default value 500Mi is valid."""
        result = _parse_size_to_gi("500Mi", max_gi=4.0)
        assert result == pytest.approx(0.48828125, rel=1e-6)

    def test_max_value_4gi(self):
        """Test max value 4Gi is valid."""
        result = _parse_size_to_gi("4Gi", max_gi=4.0)
        assert result == 4.0

    def test_exceeds_max_raises_error(self):
        """Test exceeding 4Gi max raises ValueError."""
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("5Gi", max_gi=4.0)
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("10Gi", max_gi=4.0)

    def test_valid_sizes_within_range(self):
        """Test various valid sizes within 4Gi max."""
        assert _parse_size_to_gi("100Mi", max_gi=4.0) == pytest.approx(0.09765625, rel=1e-6)
        assert _parse_size_to_gi("1Gi", max_gi=4.0) == 1.0
        assert _parse_size_to_gi("2Gi", max_gi=4.0) == 2.0
        assert _parse_size_to_gi("3Gi", max_gi=4.0) == 3.0


class TestMaxGiVariousLimits:
    """Test _parse_size_to_gi with various max_gi limits."""

    def test_max_1gi_boundary(self):
        """Test max_gi=1.0 boundary."""
        # At boundary - should pass
        assert _parse_size_to_gi("1Gi", max_gi=1.0) == 1.0
        assert _parse_size_to_gi("1024Mi", max_gi=1.0) == 1.0
        # Below boundary - should pass
        assert _parse_size_to_gi("512Mi", max_gi=1.0) == 0.5
        # Above boundary - should fail
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("1.1Gi", max_gi=1.0)
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("2Gi", max_gi=1.0)

    def test_max_10gi_boundary(self):
        """Test max_gi=10.0 boundary (storage_size limit)."""
        # At boundary - should pass
        assert _parse_size_to_gi("10Gi", max_gi=10.0) == 10.0
        # Below boundary - should pass
        assert _parse_size_to_gi("5Gi", max_gi=10.0) == 5.0
        assert _parse_size_to_gi("9Gi", max_gi=10.0) == 9.0
        # Above boundary - should fail
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("11Gi", max_gi=10.0)
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("15Gi", max_gi=10.0)

    def test_max_100gi_boundary(self):
        """Test max_gi=100.0 boundary (artifact_store_size limit)."""
        # At boundary - should pass
        assert _parse_size_to_gi("100Gi", max_gi=100.0) == 100.0
        # Below boundary - should pass
        assert _parse_size_to_gi("50Gi", max_gi=100.0) == 50.0
        assert _parse_size_to_gi("99Gi", max_gi=100.0) == 99.0
        # Above boundary - should fail
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("101Gi", max_gi=100.0)
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("200Gi", max_gi=100.0)

    def test_max_4gi_boundary(self):
        """Test max_gi=4.0 boundary (shared_cache_size limit)."""
        # At boundary - should pass
        assert _parse_size_to_gi("4Gi", max_gi=4.0) == 4.0
        assert _parse_size_to_gi("4096Mi", max_gi=4.0) == 4.0
        # Below boundary - should pass
        assert _parse_size_to_gi("3Gi", max_gi=4.0) == 3.0
        assert _parse_size_to_gi("500Mi", max_gi=4.0) == pytest.approx(0.48828125, rel=1e-6)
        # Above boundary - should fail
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("5Gi", max_gi=4.0)
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("4097Mi", max_gi=4.0)

    def test_no_max_limit(self):
        """Test with no max_gi limit (None)."""
        # Large values should pass when no limit
        assert _parse_size_to_gi("1000Gi") == 1000.0
        assert _parse_size_to_gi("500Gi") == 500.0
        assert _parse_size_to_gi("1Gi") == 1.0

    def test_fractional_max_limit(self):
        """Test with fractional max_gi limit."""
        # max_gi=0.5 (512Mi)
        assert _parse_size_to_gi("512Mi", max_gi=0.5) == 0.5
        assert _parse_size_to_gi("256Mi", max_gi=0.5) == 0.25
        with pytest.raises(ValueError, match="exceeds maximum"):
            _parse_size_to_gi("1Gi", max_gi=0.5)


# Note: The following tests require mocking the HTTP client
# since optimize() makes actual network requests.
# For now, we document the expected behavior:

# class TestOptimizeValidation:
#     """Test optimize() parameter validation.
#
#     These tests require mocking ConnectRPCClient to avoid actual network calls.
#     """
#
#     def test_cpu_with_custom_dev_shm_size_raises_error(self, mock_client):
#         """CPU 사용 시 dev_shm_size 커스텀 지정하면 오류."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         with pytest.raises(ValueError, match="can only be used with GPU"):
#             study_wrapper.optimize(
#                 lambda trial: 1.0,
#                 n_trials=1,
#                 use_gpu=False,  # CPU
#                 dev_shm_size="4Gi"  # Custom size
#             )
#
#     def test_dev_shm_size_exceeds_max_raises_error(self, mock_client):
#         """dev_shm_size max 4Gi 초과 시 오류."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         with pytest.raises(ValueError, match="exceeds maximum allowed size of 4Gi"):
#             study_wrapper.optimize(
#                 lambda trial: 1.0,
#                 n_trials=1,
#                 use_gpu=True,
#                 dev_shm_size="8Gi"  # Exceeds 4Gi
#             )
#
#     def test_tmp_cache_size_exceeds_max_raises_error(self, mock_client):
#         """tmp_cache_size max 4Gi 초과 시 오류."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         with pytest.raises(ValueError, match="exceeds maximum allowed size of 4Gi"):
#             study_wrapper.optimize(
#                 lambda trial: 1.0,
#                 n_trials=1,
#                 tmp_cache_size="10Gi"  # Exceeds 4Gi
#             )
#
#     def test_invalid_size_format_raises_error(self, mock_client):
#         """잘못된 크기 형식은 오류."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         with pytest.raises(ValueError, match="Invalid size format"):
#             study_wrapper.optimize(
#                 lambda trial: 1.0,
#                 n_trials=1,
#                 use_gpu=True,
#                 dev_shm_size="500"  # Missing unit
#             )
#
#     def test_gpu_model_sum_exceeds_n_trials(self, mock_client):
#         """gpu_model dict 합계가 n_trials 초과 시 오류."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         with pytest.raises(ValueError, match="Total GPU model allocations .* exceeds n_trials"):
#             study_wrapper.optimize(
#                 lambda trial: 1.0,
#                 n_trials=10,
#                 gpu_model={'gpu_3090': 3, 'gpu_4090': 8}  # total=11 > 10
#             )
#
#     def test_gpu_model_sum_equals_n_trials(self, mock_client):
#         """gpu_model dict 합계가 n_trials와 같을 때 성공."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         # Should succeed
#         study_wrapper.optimize(
#             lambda trial: 1.0,
#             n_trials=10,
#             gpu_model={'gpu_3090': 5, 'gpu_4090': 5}  # total=10 == 10
#         )
#
#     def test_gpu_model_sum_less_than_n_trials(self, mock_client):
#         """gpu_model dict 합계가 n_trials보다 작을 때 성공 (나머지는 Kueue 자동 배정)."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         # Should succeed
#         study_wrapper.optimize(
#             lambda trial: 1.0,
#             n_trials=10,
#             gpu_model={'gpu_3090': 3, 'gpu_4090': 4}  # total=7 < 10
#         )
#
#     def test_gpu_model_string_form(self, mock_client):
#         """gpu_model string 형태 (단일 GPU 모델 지정)."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         # Should succeed
#         study_wrapper.optimize(
#             lambda trial: 1.0,
#             n_trials=10,
#             gpu_model='gpu_4090'  # All trials use RTX 4090
#         )
#
#     def test_gpu_model_invalid_flavor(self, mock_client):
#         """유효하지 않은 GPU 모델명 에러."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         with pytest.raises(ValueError, match="Invalid GPU model"):
#             study_wrapper.optimize(
#                 lambda trial: 1.0,
#                 n_trials=10,
#                 gpu_model={'gpu_9090': 5}  # 존재하지 않는 모델
#             )
#
#     def test_gpu_model_negative_value(self, mock_client):
#         """gpu_model dict 음수 값 에러."""
#         ac = AIAutoController('<test-token>')
#         study_wrapper = ac.create_study('test-study', direction='minimize')
#
#         with pytest.raises(ValueError, match="must be positive integers"):
#             study_wrapper.optimize(
#                 lambda trial: 1.0,
#                 n_trials=10,
#                 gpu_model={'gpu_3090': -1}  # Negative value
#             )
#
