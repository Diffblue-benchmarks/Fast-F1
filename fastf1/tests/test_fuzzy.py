import pytest

from fastf1.internals.fuzzy import fuzzy_matcher
from fastf1.exceptions import FuzzyMatchError


class TestFuzzyMatcher:
    """Tests for fuzzy_matcher function"""

    def test_no_substring_matches(self):
        """Test fuzzy matching when no substring matches exist (line 88)"""
        query = "lewis"
        reference = [
            ["Max Verstappen"],
            ["Charles Leclerc"],
            ["Carlos Sainz"]
        ]

        # Should use fuzzy matching on all reference entries
        index, accurate = fuzzy_matcher(query, reference)

        # Should return an inaccurate match (False)
        assert accurate is False
        # Index should be valid
        assert 0 <= index < len(reference)

    def test_absolute_confidence_threshold_not_met(self):
        """Test that FuzzyMatchError is raised when absolute confidence is too low (line 116)"""
        query = "xyz"
        reference = [
            ["Max Verstappen"],
            ["Charles Leclerc"],
            ["Carlos Sainz"]
        ]

        # Set a high absolute confidence threshold that won't be met
        with pytest.raises(FuzzyMatchError) as excinfo:
            fuzzy_matcher(query, reference, abs_confidence=0.9)

        assert "absolute confidence" in str(excinfo.value)

    def test_relative_confidence_threshold_not_met(self):
        """Test that FuzzyMatchError is raised when relative confidence is too low (line 123)"""
        query = "max"
        reference = [
            ["Max Verstappen"],
            ["Max Smith"],  # Very similar to the first one
            ["Charles Leclerc"]
        ]

        # Set a high relative confidence threshold
        # When two matches are very similar, rel_confidence check should fail
        with pytest.raises(FuzzyMatchError) as excinfo:
            fuzzy_matcher(query, reference, rel_confidence=0.5)

        assert "relative confidence" in str(excinfo.value)

    def test_exact_substring_match(self):
        """Test that exact substring match returns accurate result"""
        query = "hamilton"
        reference = [
            ["Lewis Hamilton"],
            ["Max Verstappen"],
            ["Charles Leclerc"]
        ]

        index, accurate = fuzzy_matcher(query, reference)

        assert index == 0
        assert accurate is True

    def test_case_insensitive_matching(self):
        """Test that matching is case insensitive"""
        query = "LEWIS"
        reference = [
            ["lewis hamilton"],
            ["Max Verstappen"]
        ]

        index, accurate = fuzzy_matcher(query, reference)

        assert index == 0
        assert accurate is True

    def test_space_handling(self):
        """Test that spaces are handled correctly"""
        query = "lewis hamilton"
        reference = [
            ["LewisHamilton"],
            ["Max Verstappen"]
        ]

        index, accurate = fuzzy_matcher(query, reference)

        assert index == 0
        assert accurate is True

    def test_multiple_substring_matches(self):
        """Test fuzzy matching when multiple substring matches exist"""
        query = "max"
        reference = [
            ["Max Verstappen"],
            ["Max Smith"],
            ["Charles Leclerc"]
        ]

        # When multiple substring matches exist, fuzzy match only on those
        index, accurate = fuzzy_matcher(query, reference)

        # Should return an inaccurate match since there are multiple substring matches
        assert accurate is False
        # Index should be one of the matches
        assert index in [0, 1]

    def test_multiple_feature_strings(self):
        """Test matching with multiple feature strings per reference"""
        query = "ham"
        reference = [
            ["Lewis Hamilton", "HAM", "44"],
            ["Max Verstappen", "VER", "1"],
            ["Charles Leclerc", "LEC", "16"]
        ]

        index, accurate = fuzzy_matcher(query, reference)

        assert index == 0
        assert accurate is True

    def test_fuzzy_match_with_typo(self):
        """Test fuzzy matching handles typos"""
        query = "verstapen"  # Typo: missing 's'
        reference = [
            ["Max Verstappen"],
            ["Charles Leclerc"],
            ["Carlos Sainz"]
        ]

        index, accurate = fuzzy_matcher(query, reference)

        # Should match Verstappen despite typo
        assert index == 0
        assert accurate is False

    def test_absolute_confidence_met(self):
        """Test that matching succeeds when absolute confidence is met"""
        query = "verstapen"  # Typo to force fuzzy match
        reference = [
            ["Max Verstappen"],
            ["Charles Leclerc"]
        ]

        # Set a reasonable absolute confidence threshold
        index, accurate = fuzzy_matcher(query, reference, abs_confidence=0.7)

        assert index == 0
        assert accurate is False

    def test_relative_confidence_met(self):
        """Test that matching succeeds when relative confidence is met"""
        query = "verstapen"  # Typo to force fuzzy match
        reference = [
            ["Max Verstappen"],
            ["Charles Leclerc"],
            ["Carlos Sainz"]
        ]

        # Set a reasonable relative confidence threshold
        index, accurate = fuzzy_matcher(query, reference, rel_confidence=0.3)

        assert index == 0
        assert accurate is False
