import pytest

from fastf1.exceptions import FuzzyMatchError
from fastf1.internals.fuzzy import fuzzy_matcher


class TestFuzzyMatcherExactSubstring:
    def test_exact_substring_single_match(self):
        reference = [['Australia'], ['Bahrain'], ['Monaco']]
        index, accurate = fuzzy_matcher('australia', reference)
        assert index == 0
        assert accurate is True

    def test_exact_substring_case_insensitive(self):
        reference = [['Australia'], ['Bahrain'], ['Monaco']]
        index, accurate = fuzzy_matcher('BAHRAIN', reference)
        assert index == 1
        assert accurate is True

    def test_exact_substring_ignores_spaces(self):
        reference = [['Abu Dhabi'], ['Bahrain'], ['Monaco']]
        index, accurate = fuzzy_matcher('abu dhabi', reference)
        assert index == 0
        assert accurate is True

    def test_partial_substring_match(self):
        reference = [['Australian Grand Prix'], ['Bahrain GP'], ['Monaco GP']]
        index, accurate = fuzzy_matcher('australian', reference)
        assert index == 0
        assert accurate is True

    def test_multiple_feature_strings(self):
        reference = [
            ['Australia', 'Melbourne'],
            ['Bahrain', 'Sakhir'],
            ['Monaco', 'Monte Carlo'],
        ]
        index, accurate = fuzzy_matcher('melbourne', reference)
        assert index == 0
        assert accurate is True


class TestFuzzyMatcherFuzzy:
    def test_fuzzy_match_returns_inaccurate(self):
        reference = [['Australia'], ['Bahrain'], ['Monaco']]
        index, accurate = fuzzy_matcher('monacooo', reference)
        assert index == 2
        assert accurate is False

    def test_fuzzy_match_closest(self):
        reference = [['Australia'], ['Austria'], ['Monaco']]
        index, accurate = fuzzy_matcher('austral', reference)
        # 'austral' is a substring of 'australia' but also of 'austria'
        # so it falls to fuzzy matching; 'australia' should be closer
        assert index == 0

    def test_multiple_substring_matches_uses_fuzzy(self):
        # 'austria' is an exact substring of 'austria' only (not 'australia')
        # so it returns as an accurate single substring match
        reference = [['Australia'], ['Austria'], ['Monaco']]
        index, accurate = fuzzy_matcher('austria', reference)
        assert index == 1


class TestFuzzyMatcherConfidence:
    def test_abs_confidence_raises_on_low_match(self):
        reference = [['zzzzzzzzz'], ['yyyyyyyyy']]
        with pytest.raises(FuzzyMatchError):
            fuzzy_matcher('abcdefgh', reference, abs_confidence=0.9)

    def test_rel_confidence_raises_on_close_matches(self):
        reference = [['abc'], ['abd']]
        with pytest.raises(FuzzyMatchError):
            fuzzy_matcher('abx', reference, rel_confidence=0.9)

    def test_confidence_zero_disables_check(self):
        reference = [['zzzzzzzzz'], ['yyyyyyyyy']]
        # should not raise with confidence disabled
        index, accurate = fuzzy_matcher(
            'abcdefgh', reference,
            abs_confidence=0.0, rel_confidence=0.0
        )
        assert int(index) == index  # numpy int or python int
