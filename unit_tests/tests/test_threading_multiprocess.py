import pytest
from unittest.mock import patch, MagicMock

def test_generate_pii_text_basic():
    """Базовый тест генерации PII текста"""
    from src.threadings_multiprocess import generate_pii_text
    
    text = generate_pii_text()
    assert isinstance(text, str)
    assert len(text) > 0

def test_generate_test_data_basic():
    """Базовый тест генерации тестовых данных"""
    from src.threadings_multiprocess import generate_test_data
    
    data = generate_test_data(num_files=2, lines_per_file=1)
    assert len(data) == 2
    assert isinstance(data[0], tuple)

def test_hash_mask_function():
    """Тест функции маскировки"""
    from src.threadings_multiprocess import hash_mask
    
    original = "test@example.com"
    masked = hash_mask(original)
    
    assert isinstance(masked, str)
    assert len(masked) == 10
    assert masked != original

def test_replacer_function():
    """Тест функции замены"""
    from src.threadings_multiprocess import replacer
    from unittest.mock import MagicMock
    
    mock_match = MagicMock()
    mock_match.group.return_value = "test@example.com"
    
    result = replacer(mock_match)
    assert isinstance(result, str)
    assert len(result) == 10

def test_patterns_defined():
    """Тест что паттерны определены"""
    from src.threadings_multiprocess import patterns
    
    assert len(patterns) == 3
    for pattern in patterns:
        assert hasattr(pattern, 'findall')
        assert hasattr(pattern, 'sub')

def test_find_pii_in_content_signature():
    """Тест сигнатуры функции find_pii_in_content"""
    from src.threadings_multiprocess import find_pii_in_content
    
    mock_queue = MagicMock()
    mock_lock = MagicMock()
    
    find_pii_in_content("test.txt", "content", mock_queue, mock_lock)
    
    mock_queue.put.assert_called_once()

def test_mp_worker_signature():
    """Тест сигнатуры функции mp_worker"""
    from src.threadings_multiprocess import mp_worker
    
    mock_queue = MagicMock()
    
    with patch('src.threadings_multiprocess.test_data', [("file1", "content1"), ("file2", "content2")]):

        mp_worker(0, 2, mock_queue)
        
        assert mock_queue.put.call_count == 2

def test_module_imports():
    """Тест что все функции импортируются"""
    from src.threadings_multiprocess import (
        generate_pii_text,
        generate_test_data,
        find_pii_in_content,
        hash_mask,
        replacer,
        mp_worker,
        patterns
    )
    
    assert callable(generate_pii_text)
    assert callable(generate_test_data)
    assert callable(find_pii_in_content)
    assert callable(hash_mask)
    assert callable(replacer)
    assert callable(mp_worker)
    assert isinstance(patterns, list)

@patch('src.threadings_multiprocess.ThreadPoolExecutor')
def test_threading_version_mocked(mock_executor):
    """Тест threading версии с моками"""
    from src.threadings_multiprocess import threading_version
    
    mock_executor_instance = MagicMock()
    mock_executor.return_value.__enter__.return_value = mock_executor_instance
    
    test_data = [("file1", "content1")]
    results = threading_version(test_data)
    
    assert mock_executor_instance.submit.call_count == 1

@patch('src.threadings_multiprocess.multiprocessing.Process')
@patch('src.threadings_multiprocess.multiprocessing.Queue')
def test_multiprocessing_version_mocked(mock_queue, mock_process):
    """Тест multiprocessing версии с моками"""
    from src.threadings_multiprocess import multiprocessing_version
    
    mock_queue_instance = MagicMock()
    mock_queue_instance.empty.side_effect = [False, True]
    mock_queue_instance.get.return_value = ("file1", 100)
    mock_queue.return_value = mock_queue_instance
    
    mock_process_instance = MagicMock()
    mock_process.return_value = mock_process_instance
    
    test_data = [("file1", "content1")]
    results = multiprocessing_version(test_data)
    
    assert mock_process.call_count > 0
