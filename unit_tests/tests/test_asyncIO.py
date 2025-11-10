import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.AsyncIO import (
    generate_pii_text,
    generate_test_data,
    find_pii_in_content,
    hash_mask,
    replacer,
    mask_content,
    async_threading_version,
    async_multiprocessing_version,
    email_pattern,
    phone_pattern,
    ssn_pattern
)

class TestAsyncIO:
    
    def test_generate_pii_text(self):
        text = generate_pii_text()
        assert isinstance(text, str)
        assert len(text) > 0
        assert (email_pattern.search(text) or 
                phone_pattern.search(text) or 
                ssn_pattern.search(text))
    
    def test_generate_test_data(self):
        data = generate_test_data(num_files=2, lines_per_file=3)
        assert len(data) == 2
        for filename, content in data:
            assert filename.startswith("file_")
            assert isinstance(content, str)
            assert content.count('\n') == 2
    
    def test_find_pii_in_content(self):
        test_content = "test@example.com +1-555-123-4567 123-45-6789"
        filename = "test.txt"
        result = find_pii_in_content(filename, test_content)
        assert result[0] == filename
        assert result[1] == 3
    
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
    
    def test_mask_content(self):
        filename = "test.txt"
        content = "Contact: test@example.com"
        result_filename, result_length = mask_content(filename, content)
        assert result_filename == filename
        assert result_length > 0
    
    @pytest.mark.asyncio
    async def test_async_threading_version(self):
        test_data = [("file1.txt", "email@test.com"), ("file2.txt", "phone +1-555-123-4567")]
        results = await async_threading_version(test_data)
        assert len(results) == len(test_data)
        for filename, count in results:
            assert isinstance(filename, str)
            assert isinstance(count, int)
    
    @pytest.mark.asyncio
    async def test_async_multiprocessing_version(self):
        test_data = [("file1.txt", "email@test.com"), ("file2.txt", "phone +1-555-123-4567")]
        results = await async_multiprocessing_version(test_data)
        assert len(results) == len(test_data)
        for filename, length in results:
            assert isinstance(filename, str)
            assert isinstance(length, int)
    
    def test_regex_patterns(self):
        test_cases = [
            ("test@example.com", email_pattern, True),
            ("invalid-email", email_pattern, False),
            ("+1-555-123-4567", phone_pattern, True),
            ("555-123-4567", phone_pattern, False),
            ("123-45-6789", ssn_pattern, True),
            ("12-345-6789", ssn_pattern, False),
        ]
        
        for text, pattern, should_match in test_cases:
            if should_match:
                assert pattern.search(text) is not None, f"Pattern failed for: {text}"
            else:
                assert pattern.search(text) is None, f"Pattern incorrectly matched: {text}"
