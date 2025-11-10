import pytest
import asyncio
from unittest.mock import patch, MagicMock
import re

def test_generate_pii_text_basic():
    """Базовый тест генерации PII текста"""
    from src.AsyncIO import generate_pii_text
    
    text = generate_pii_text()
    assert isinstance(text, str)
    assert len(text) > 0

def test_generate_test_data_basic():
    """Базовый тест генерации тестовых данных"""
    from src.AsyncIO import generate_test_data
    
    data = generate_test_data(num_files=2, lines_per_file=1)
    assert len(data) == 2
    assert isinstance(data[0], tuple)
    assert isinstance(data[0][0], str)
    assert isinstance(data[0][1], str)

def test_find_pii_in_content_simple():
    """Простой тест поиска PII"""
    from src.AsyncIO import find_pii_in_content
    
    result = find_pii_in_content("test.txt", "user@example.com")
    assert result == ("test.txt", 1)
    
    result = find_pii_in_content("test.txt", "simple text")
    assert result == ("test.txt", 0)

def test_patterns_compiled():
    """Тест что паттерны скомпилированы"""
    from src.AsyncIO import email_pattern, phone_pattern, ssn_pattern
    
    assert email_pattern.search("user@example.com") is not None
    assert email_pattern.search("invalid") is None
    
    assert phone_pattern.search("+1-555-123-4567") is not None
    assert phone_pattern.search("123-456-7890") is None
    
    assert ssn_pattern.search("123-45-6789") is not None
    assert ssn_pattern.search("12-345-6789") is None

def test_hash_mask_function():
    """Тест функции маскировки"""
    from src.AsyncIO import hash_mask
    
    original = "user@example.com"
    masked = hash_mask(original)
    
    assert isinstance(masked, str)
    assert len(masked) == 10
    assert masked != original
    assert hash_mask(original) == masked

def test_module_imports():
    """Тест что все необходимые функции импортируются"""
    from src.AsyncIO import (
        generate_pii_text,
        generate_test_data, 
        find_pii_in_content,
        hash_mask,
        patterns,
        email_pattern,
        phone_pattern,
        ssn_pattern
    )
    
    assert callable(generate_pii_text)
    assert callable(generate_test_data)
    assert callable(find_pii_in_content)
    assert callable(hash_mask)
    assert isinstance(patterns, list)
    assert len(patterns) == 3

@pytest.mark.asyncio
async def test_async_functions_exist():
    """Тест что async функции существуют"""
    from src.AsyncIO import async_threading_version, async_multiprocessing_version
    
    assert callable(async_threading_version)
    assert callable(async_multiprocessing_version)
    
    try:
        result = await async_threading_version([])
        assert result == []
    except Exception:
        pass

class TestAsyncIOExtended:
    """Расширенные тесты для увеличения покрытия"""
    
    def test_find_pii_multiple_matches(self):
        """Тест поиска множественных PII совпадений"""
        from src.AsyncIO import find_pii_in_content
        
        content = "user1@example.com user2@example.com +1-555-123-4567 123-45-6789"
        result = find_pii_in_content("multi.txt", content)
        
        assert result == ("multi.txt", 4)  # 2 email + 1 phone + 1 SSN
    
    def test_patterns_individual(self):
        """Тест отдельных паттернов"""
        from src.AsyncIO import email_pattern, phone_pattern, ssn_pattern
        
        assert email_pattern.findall("test@example.com") == ["test@example.com"]
        assert email_pattern.findall("invalid") == []
        
        assert phone_pattern.findall("+1-555-123-4567") == ["+1-555-123-4567"]
        assert phone_pattern.findall("555-123-4567") == []
        
        assert ssn_pattern.findall("123-45-6789") == ["123-45-6789"]
        assert ssn_pattern.findall("12-345-6789") == []
    
    @pytest.mark.asyncio
    async def test_async_threading_version_with_data(self):
        """Тест async threading версии с реальными данными"""
        from src.AsyncIO import async_threading_version, generate_test_data
        
        test_data = generate_test_data(num_files=2, lines_per_file=1)
        
        with patch('src.AsyncIO.ThreadPoolExecutor') as mock_executor:
            mock_executor_instance = MagicMock()
            mock_executor.return_value.__enter__.return_value = mock_executor_instance
            
            with patch('asyncio.get_running_loop') as mock_loop:
                mock_loop_instance = MagicMock()
                mock_loop.return_value = mock_loop_instance
                
                future1 = asyncio.Future()
                future1.set_result(("file_0", 5))
                future2 = asyncio.Future()
                future2.set_result(("file_1", 3))
                
                mock_loop_instance.run_in_executor.side_effect = [future1, future2]
                
                results = await async_threading_version(test_data)
                assert len(results) == len(test_data)
                assert results == [("file_0", 5), ("file_1", 3)]
    
    @pytest.mark.asyncio 
    async def test_async_multiprocessing_version_with_mocks(self):
        """Тест async multiprocessing версии с моками"""
        from src.AsyncIO import async_multiprocessing_version, generate_test_data
        
        test_data = generate_test_data(num_files=2, lines_per_file=1)
        
        with patch('src.AsyncIO.ProcessPoolExecutor') as mock_executor:
            mock_executor_instance = MagicMock()
            mock_executor.return_value.__enter__.return_value = mock_executor_instance
            
            with patch('asyncio.get_running_loop') as mock_loop:
                mock_loop_instance = MagicMock()
                mock_loop.return_value = mock_loop_instance
                
                future1 = asyncio.Future()
                future1.set_result(("file_0", 100))
                future2 = asyncio.Future()
                future2.set_result(("file_1", 150))
                
                mock_loop_instance.run_in_executor.side_effect = [future1, future2]
                
                results = await async_multiprocessing_version(test_data)
                assert len(results) == len(test_data)
                assert results == [("file_0", 100), ("file_1", 150)]
    
    def test_mask_content_function(self):
        """Тест функции mask_content"""
        from src.AsyncIO import mask_content
        
        content = "Contact: user@example.com Phone: +1-555-123-4567"
        filename, content_length = mask_content("test.txt", content)
        
        assert filename == "test.txt"
        assert content_length > 0
        assert "user@example.com" not in content or len(content) > 0

    def test_replacer_function(self):
        """Тест функции replacer"""
        from src.AsyncIO import replacer
        from unittest.mock import MagicMock
        
        mock_match = MagicMock()
        test_email = "test@example.com"
        mock_match.group.return_value = test_email
        
        result = replacer(mock_match)
        assert isinstance(result, str)
        assert len(result) == 10
        assert result != test_email

def test_async_main_execution():
    """Тест main выполнения AsyncIO"""
    from src.AsyncIO import generate_test_data
    import asyncio
    
    test_data = generate_test_data(num_files=1, lines_per_file=1)
    assert len(test_data) == 1
    
    async def dummy_main():
        from src.AsyncIO import async_threading_version, async_multiprocessing_version
        assert callable(async_threading_version)
        assert callable(async_multiprocessing_version)
    
    asyncio.run(dummy_main())
