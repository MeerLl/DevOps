import pytest
import time
import platform
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from src.soft_timeout import TimeoutConfig, soft_timeout

class TestTimeoutConfig:
    
    def test_timeout_config(self):
        config = TimeoutConfig(seconds=5)
        assert config.seconds == 5

    def test_timeout_config_validation(self):
        with pytest.raises(ValidationError):
            TimeoutConfig(seconds=-1)
        
        with pytest.raises(ValidationError):
            TimeoutConfig(seconds=0)

class TestSoftTimeoutCommon:
    
    def test_soft_timeout_basic(self):
        with soft_timeout(10):
            print("Basic timeout test")
        assert True

    def test_soft_timeout_validation(self):
        with pytest.raises(ValidationError):
            with soft_timeout(-5):
                pass

class TestSoftTimeoutPlatformSpecific:
    """Тесты для платформо-специфичного поведения"""
    
    @patch('src.soft_timeout.platform.system')
    def test_windows_behavior(self, mock_system):
        """Тест поведения на Windows"""
        mock_system.return_value = 'Windows'
        
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            with soft_timeout(1):
                print("Windows operation")
            
            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)
            assert "not supported on Windows" in str(w[0].message)
    
    @patch('src.soft_timeout.platform.system')
    def test_unix_behavior(self, mock_system):
        """Тест поведения на Unix системах"""
        mock_system.return_value = 'Linux'
        
        with soft_timeout(5):
            print("Unix operation")
        
        assert True

class TestSoftTimeoutEdgeCases:
    """Тесты для граничных случаев soft-timeout"""
    
    def test_very_short_valid_timeout(self):
        config = TimeoutConfig(seconds=1)
        assert config.seconds == 1
        
        with soft_timeout(1):
            print("Short timeout test")
    
    def test_large_timeout_value(self):
        config = TimeoutConfig(seconds=3600)
        assert config.seconds == 3600
        
        with soft_timeout(3600):
            print("Large timeout test")

class TestSoftTimeoutExtended:
    """Расширенные тесты для soft_timeout"""
    
    def test_timeout_config_positive_int(self):
        """Тест TimeoutConfig с положительными целыми"""
        from src.soft_timeout import TimeoutConfig
        
        config = TimeoutConfig(seconds=1)
        assert config.seconds == 1
        
        config = TimeoutConfig(seconds=1000)
        assert config.seconds == 1000
    
    def test_soft_timeout_context_manager(self):
        """Тест soft_timeout как context manager"""
        from src.soft_timeout import soft_timeout
        
        with soft_timeout(5):
            x = 1 + 1
            assert x == 2
    
    @patch('src.soft_timeout.platform.system')
    def test_unix_signal_handling(self, mock_system):
        """Тест обработки сигналов на Unix"""
        mock_system.return_value = 'Linux'
        
        from src.soft_timeout import soft_timeout
        import signal
        
        with patch('signal.signal') as mock_signal, \
             patch('signal.alarm') as mock_alarm:
            
            mock_old_handler = MagicMock()
            mock_signal.return_value = mock_old_handler
            
            with soft_timeout(3):
                pass
            
            mock_signal.assert_called()
            mock_alarm.assert_any_call(3)  
            mock_alarm.assert_called_with(0)  
    
    @patch('src.soft_timeout.platform.system') 
    def test_windows_warning(self, mock_system):
        """Тест предупреждения на Windows"""
        mock_system.return_value = 'Windows'
        
        from src.soft_timeout import soft_timeout
        import warnings
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            with soft_timeout(5):
                pass
            
            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)
            assert "Windows" in str(w[0].message)
    
    def test_validation_error_propagation(self):
        """Тест распространения ошибок валидации"""
        from src.soft_timeout import soft_timeout
        
        with pytest.raises(Exception):
            with soft_timeout(0): 
                pass
        
        with pytest.raises(Exception):
            with soft_timeout(-1):  
                pass

class TestSoftTimeoutComplete:
    """Тесты для полного покрытия soft_timeout"""
    
    def test_soft_timeout_with_exception_inside(self):
        """Тест soft_timeout с исключением внутри блока"""
        from src.soft_timeout import soft_timeout
        
        with patch('src.soft_timeout.platform.system', return_value='Linux'):
            with patch('signal.signal') as mock_signal, \
                 patch('signal.alarm') as mock_alarm:
                
                mock_old_handler = MagicMock()
                mock_signal.return_value = mock_old_handler
                
                try:
                    with soft_timeout(5):
                        raise ValueError("Test exception inside timeout")
                except ValueError:
                    pass 
                
                mock_alarm.assert_called_with(0)
    
    def test_soft_timeout_very_short_timeout(self):
        """Тест с очень коротким таймаутом"""
        from src.soft_timeout import soft_timeout
        
        with patch('src.soft_timeout.platform.system', return_value='Linux'):
            with soft_timeout(1):
                result = 2 + 2
                assert result == 4
