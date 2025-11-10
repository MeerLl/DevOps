import pytest
import time
import platform
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from src.soft_timeout import soft_timeout, TimeoutConfig, TimeoutError

class TestTimeoutConfig:
    
    def test_valid_config(self):
        config = TimeoutConfig(seconds=5)
        assert config.seconds == 5
    
    def test_positive_integer_validation(self):
        with pytest.raises(ValidationError):
            TimeoutConfig(seconds=-1)
        with pytest.raises(ValidationError):
            TimeoutConfig(seconds=0)
    
    def test_float_validation(self):
        with pytest.raises(ValidationError):
            TimeoutConfig(seconds=2.5)

class TestSoftTimeoutUnix:
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix specific test")
    def test_timeout_raises_error_unix(self):
        with pytest.raises(TimeoutError, match="Operation timed out"):
            with soft_timeout(1):
                time.sleep(2)
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix specific test")
    def test_no_timeout_within_limit_unix(self):
        try:
            with soft_timeout(2):
                time.sleep(1)
            assert True
        except TimeoutError:
            pytest.fail("Unexpected TimeoutError")
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix specific test")
    def test_invalid_timeout_value_unix(self):
        with pytest.raises(ValidationError):
            with soft_timeout(0):
                pass

class TestSoftTimeoutWindows:
    
    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows specific test")
    def test_windows_no_op_with_warning(self):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with soft_timeout(1):
                time.sleep(2)
            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)
            assert "not supported on Windows" in str(w[0].message)

class TestSoftTimeoutCommon:
    
    def test_context_manager_cleanup(self):
        with soft_timeout(5):
            print("Working inside context")
        assert True
    
    def test_negative_timeout_validation(self):
        with pytest.raises(ValidationError):
            with soft_timeout(-5):
                pass
    
    @patch('src.soft_timeout.platform.system')
    def test_cross_platform_behavior(self, mock_system):
        mock_system.return_value = "Linux"
        with pytest.raises(TimeoutError):
            with soft_timeout(1):
                time.sleep(1.5)
        mock_system.return_value = "Windows"
        try:
            with soft_timeout(1):
                time.sleep(1.5)
        except TimeoutError:
            pytest.fail("TimeoutError should not be raised on Windows")

class TestSoftTimeoutIntegration:
    
    def test_nested_timeouts(self):
        try:
            with soft_timeout(10):
                with soft_timeout(5):
                    time.sleep(1)
        except Exception as e:
            pytest.fail(f"Unexpected exception in nested timeouts: {e}")
    
    def test_timeout_with_exceptions(self):
        with pytest.raises(ValueError, match="Internal error"):
            with soft_timeout(5):
                raise ValueError("Internal error")

class TestSoftTimeoutEdgeCases:
    
    def test_very_short_timeout(self):
        with pytest.raises(ValidationError):
            with soft_timeout(0)
    
    def test_very_long_timeout(self):
        try:
            with soft_timeout(3600):
                time.sleep(0.1)
        except Exception as e:
            pytest.fail(f"Unexpected exception with long timeout: {e}")
    
    def test_timeout_value_types(self):
        with pytest.raises(ValidationError):
            with soft_timeout("5")
        with pytest.raises(ValidationError):
            with soft_timeout(5.0)
