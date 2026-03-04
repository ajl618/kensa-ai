"""
Tests for test packs.
"""

import pytest

from kensa_ai.test_packs import load_test_pack, load_category_tests
from kensa_ai.core.test_case import TestCase, PromptBasedTest, Severity


class TestTestPacks:
    """Tests for test pack loading."""
    
    def test_load_basic_security_pack(self):
        """Test loading basic security pack."""
        tests = load_test_pack("basic_security")
        
        assert len(tests) > 0
        assert all(isinstance(t, TestCase) for t in tests)
    
    def test_load_full_security_pack(self):
        """Test loading full security pack."""
        tests = load_test_pack("full_security")
        
        assert len(tests) > 0
        # Full pack should have more tests than basic
        basic_tests = load_test_pack("basic_security")
        assert len(tests) >= len(basic_tests)
    
    def test_load_with_category_filter(self):
        """Test loading with category filter."""
        tests = load_test_pack("full_security", categories=["prompt_injection"])
        
        assert len(tests) > 0
        assert all(t.category == "prompt_injection" for t in tests)
    
    def test_load_with_max_per_category(self):
        """Test loading with max tests per category."""
        tests = load_test_pack("full_security", max_per_category=5)
        
        # Count tests per category
        category_counts = {}
        for test in tests:
            category_counts[test.category] = category_counts.get(test.category, 0) + 1
        
        assert all(count <= 5 for count in category_counts.values())


class TestCategoryTests:
    """Tests for individual category test loading."""
    
    def test_load_prompt_injection(self):
        """Test loading prompt injection tests."""
        tests = load_category_tests("prompt_injection")
        
        assert len(tests) > 0
        assert all(t.category == "prompt_injection" for t in tests)
    
    def test_load_jailbreak(self):
        """Test loading jailbreak tests."""
        tests = load_category_tests("jailbreak")
        
        assert len(tests) > 0
        assert all(t.category == "jailbreak" for t in tests)
    
    def test_load_data_leakage(self):
        """Test loading data leakage tests."""
        tests = load_category_tests("data_leakage")
        
        assert len(tests) > 0
        assert all(t.category == "data_leakage" for t in tests)


class TestPromptBasedTest:
    """Tests for prompt-based test case."""
    
    def test_prompt_generation(self):
        """Test prompt generation."""
        test = PromptBasedTest(
            name="test",
            prompt="Test prompt",
            category="general",
        )
        
        assert test.generate_prompt() == "Test prompt"
    
    def test_evaluation_pass(self):
        """Test evaluation that should pass."""
        test = PromptBasedTest(
            name="test",
            prompt="harmful request",
            category="general",
            failure_patterns=["harmful_response"],
            success_patterns=["cannot help"],
        )
        
        result = test.evaluate("I cannot help with that request.")
        
        assert result.passed is True
    
    def test_evaluation_fail(self):
        """Test evaluation that should fail."""
        test = PromptBasedTest(
            name="test",
            prompt="harmful request",
            category="general",
            failure_patterns=["here is how"],
            success_patterns=[],
        )
        
        result = test.evaluate("Here is how to do that harmful thing.")
        
        assert result.passed is False
    
    def test_severity_levels(self):
        """Test different severity levels."""
        for severity in Severity:
            test = PromptBasedTest(
                name="test",
                prompt="test",
                category="general",
                severity=severity,
            )
            assert test.severity == severity
