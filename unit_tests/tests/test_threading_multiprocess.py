import pytest
import re
import time
from unittest.mock import patch, MagicMock
from src.threading_multiprocess import (
    generate_pii_text,
    generate_test_data,
    find_pii_in_content,
    hash_mask,
    replacer,
    threading_version,
    multiprocessing_version,
    email_pattern,
    phone_pattern,
    ssn_pattern
)

class TestThreadingMultiprocess:
    
    def test_generate_pii_text(self):
        text = generate_pii_text()
        assert isinstance(text, str)
        assert len(text) > 0
        has_pii = (email_pattern.search(text) or 
                   phone_pattern.search(text) or 
                   ssn_pattern.search(text))
        assert has_pii
    
    def test_generate_test_data(self):
        data = generate_test_data(num_files=3, lines_per_file=2)
        assert len(data) == 3
        for filename, content in data:
            assert filename.startswith("file_")
            assert isinstance(content, str)
            lines = content.split('\n')
            assert len(lines) == 2
    
    def test_find_pii_in_content(self):
        test_content = "email: test@example.com, phone: +1-555-123-4567, ssn: 123-45-6789"
        filename = "test.txt"
        result = find_pii_in_content(filename, test_content, MagicMock(), MagicMock())
        assert result is None
    
    def test_hash_mask(self):
        test_pii = "test@example.com"
        masked = hash_mask(test_pii)
        assert isinstance(masked, str)
        assert len(masked) == 10
        assert all(c in '0123456789abcdef' for c in masked)
    
    def test_replacer(self):
        mock_match = MagicMock()
        mock_match.group.return_value = "test@example.com"
        result = replacer(mock_match)
        assert isinstance(result, str)
        assert len(result) == 10
    
    @patch('src.threading_multiprocess.ThreadPoolExecutor')
    def test_threading_version(self, mock_executor):
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        test_data = [("file1.txt", "email@test.com"), ("file2.txt", "phone +1-555-123-4567")]
        results = threading_version(test_data)
        assert isinstance(results, list)
        assert mock_executor_instance.submit.call_count == len(test_data)
    
    @patch('src.threading_multiprocess.multiprocessing.Process')
    @patch('src.threading_multiprocess.multiprocessing.Queue')
    def test_multiprocessing_version(self, mock_queue, mock_process):
        mock_queue_instance = MagicMock()
        mock_queue.return_value = mock_queue_instance
        mock_queue_instance.empty.side_effect = [False, False, True]
        mock_queue_instance.get.side_effect = [("file1", 100), ("file2", 200)]
        mock_process_instance = MagicMock()
        mock_process.return_value = mock_process_instance
        test_data = [("file1.txt", "content1"), ("file2.txt", "content2")]
        results = multiprocessing_version(test_data)
        assert isinstance(results, list)
        assert len(results) == 2
        assert results == [("file1", 100), ("file2", 200)]
    
    def test_regex_patterns_comprehensive(self):
        test_cases = [
            ("test@example.com", ["test@example.com"], [], []),
            ("+1-555-123-4567", [], ["+1-555-123-4567"], []),
            ("123-45-6789", [], [], ["123-45-6789"]),
            ("mixed test@domain.com and +1-555-987-6543", 
             ["test@domain.com"], ["+1-555-987-6543"], []),
            ("no pii here", [], [], []),
        ]
        
        for text, exp_email, exp_phone, exp_ssn in test_cases:
            found_email = email_pattern.findall(text)
            found_phone = phone_pattern.findall(text)
            found_ssn = ssn_pattern.findall(text)
            assert found_email == exp_email, f"Email mismatch for: {text}"
            assert found_phone == exp_phone, f"Phone mismatch for: {text}"
            assert found_ssn == exp_ssn, f"SSN mismatch for: {text}"

class TestPerformanceCharacteristics:
    
    def test_threading_version_performance(self):
        small_data = generate_test_data(num_files=5, lines_per_file=10)
        start_time = time.time()
        results = threading_version(small_data)
        execution_time = time.time() - start_time
        assert execution_time < 10.0
        assert len(results) == len(small_data)
