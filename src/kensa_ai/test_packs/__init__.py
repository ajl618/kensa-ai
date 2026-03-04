"""
Test packs for Kensa-AI.
"""

from pathlib import Path
from typing import Optional

import yaml

from kensa_ai.core.test_case import TestCase, PromptBasedTest, Severity


# Test pack registry
TEST_PACKS = {
    "basic_security": "basic_security",
    "full_security": "full_security",
    "ci_quick": "ci_quick",
    "prompt_injection": "prompt_injection",
    "jailbreak": "jailbreak",
    "data_leakage": "data_leakage",
    "toxicity": "toxicity",
    "hallucination": "hallucination",
}


def load_test_pack(
    pack_name: str,
    categories: Optional[list[str]] = None,
    max_per_category: int = 50,
) -> list[TestCase]:
    """
    Load tests from a test pack.
    
    Args:
        pack_name: Name of the test pack
        categories: Optional list of categories to filter
        max_per_category: Maximum tests per category
        
    Returns:
        List of TestCase instances
    """
    tests = []
    
    # Determine which categories to load
    if pack_name in ["basic_security", "ci_quick"]:
        pack_categories = ["prompt_injection", "jailbreak", "data_leakage"]
    elif pack_name == "full_security":
        pack_categories = ["prompt_injection", "jailbreak", "data_leakage", "toxicity", "hallucination"]
    else:
        pack_categories = [pack_name]
    
    # Filter by requested categories
    if categories:
        pack_categories = [c for c in pack_categories if c in categories]
    
    # Load tests from each category
    for category in pack_categories:
        category_tests = load_category_tests(category, max_per_category)
        tests.extend(category_tests)
    
    return tests


def load_category_tests(category: str, max_tests: int = 50) -> list[TestCase]:
    """Load tests for a specific category."""
    from kensa_ai.test_packs import prompt_injection
    from kensa_ai.test_packs import jailbreak
    from kensa_ai.test_packs import data_leakage
    from kensa_ai.test_packs import toxicity
    from kensa_ai.test_packs import hallucination
    
    category_modules = {
        "prompt_injection": prompt_injection,
        "jailbreak": jailbreak,
        "data_leakage": data_leakage,
        "toxicity": toxicity,
        "hallucination": hallucination,
    }
    
    module = category_modules.get(category)
    if module is None:
        return []
    
    tests = module.get_tests()
    return tests[:max_tests]


def load_prompts_from_yaml(yaml_path: Path, category: str) -> list[TestCase]:
    """Load test prompts from a YAML file."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    
    tests = []
    for item in data.get("prompts", []):
        test = PromptBasedTest(
            name=item.get("name", "unnamed"),
            prompt=item["prompt"],
            category=category,
            severity=Severity(item.get("severity", "medium")),
            success_patterns=item.get("success_patterns", []),
            failure_patterns=item.get("failure_patterns", []),
            description=item.get("description", ""),
            tags=item.get("tags", []),
        )
        tests.append(test)
    
    return tests


__all__ = [
    "load_test_pack",
    "load_category_tests",
    "load_prompts_from_yaml",
    "TEST_PACKS",
]
