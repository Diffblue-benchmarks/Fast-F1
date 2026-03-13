import pytest

from fastf1._api import make_path


class TestMakePath:
    def test_basic_path(self):
        result = make_path('Italian Grand Prix', '2019-09-08',
                           'Qualifying', '2019-09-07')
        assert result == '/static/2019/2019-09-08_Italian_Grand_Prix/2019-09-07_Qualifying/'

    def test_spaces_replaced_with_underscores(self):
        result = make_path('Test Event', '2022-03-10',
                           'Practice 1', '2022-03-10')
        assert ' ' not in result

    def test_brazil_qualifying_workaround(self):
        result = make_path('São Paulo Grand Prix', '2024-11-03',
                           'Qualifying', '2024-11-03')
        assert '2024-11-02_Qualifying' in result

    def test_2025_preseason_testing_day1(self):
        result = make_path('Pre-Season Testing', '2025-02-28',
                           'Practice 1', '2025-02-26')
        assert '2025-02-26_Day_1' in result

    def test_2025_preseason_testing_day2(self):
        result = make_path('Pre-Season Testing', '2025-02-28',
                           'Practice 2', '2025-02-27')
        assert '2025-02-27_Day_2' in result

    def test_2025_preseason_testing_day3(self):
        result = make_path('Pre-Season Testing', '2025-02-28',
                           'Practice 3', '2025-02-28')
        assert '2025-02-28_Day_3' in result

    def test_2026_preseason_testing(self):
        result = make_path('Pre-Season Testing', '2026-02-13',
                           'Practice 1', '2026-02-11')
        assert '2026-02-11_Day_1' in result

    def test_path_starts_with_static(self):
        result = make_path('Any GP', '2023-05-07',
                           'Race', '2023-05-07')
        assert result.startswith('/static/')

    def test_path_ends_with_slash(self):
        result = make_path('Any GP', '2023-05-07',
                           'Race', '2023-05-07')
        assert result.endswith('/')

    def test_year_extracted_correctly(self):
        result = make_path('Any GP', '2023-05-07',
                           'Race', '2023-05-07')
        assert '/2023/' in result
