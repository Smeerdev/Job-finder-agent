from datetime import UTC, datetime

from intern_engine import filters

CYCLES = ["2026 Graduates"]


class TestInternship:
    def test_matches_intern(self):
        assert filters.is_internship("Software Engineer Intern")
        assert filters.is_internship("Data Co-op")

    def test_rejects_substring_false_positive(self):
        # "internal" / "international" must not count as internships
        assert not filters.is_internship("Internal Tools Engineer")
        assert not filters.is_internship("International Operations")

    def test_rejects_senior(self):
        assert not filters.is_internship("Senior Software Intern")


class TestTech:
    def test_keeps_software_and_ml(self):
        assert filters.is_tech("Software Engineer Intern")
        assert filters.is_tech("Machine Learning Intern")
        assert filters.is_tech("Backend Developer Intern")

    def test_drops_non_tech_and_hardware(self):
        assert not filters.is_tech("Mechanical Engineering Intern")
        assert not filters.is_tech("Technical Recruiting Intern")
        assert not filters.is_tech("FPGA Hardware Intern")

    def test_drops_phd(self):
        assert not filters.is_tech("PhD Machine Learning Intern")


class TestSeason:
    def test_explicit_cycle(self):
        assert filters.detect_season("SWE Intern, 2026", CYCLES) == "2026 Graduates"

class TestRegion:
    def test_us_match(self):
        assert filters.region_ok("San Francisco, CA", want_us=True, want_canada=False)
        assert filters.region_ok("New York, United States", want_us=True, want_canada=False)

    def test_canada_excluded_when_us_only(self):
        assert not filters.region_ok("Toronto, Ontario, Canada", want_us=True, want_canada=False)
        assert filters.region_ok("Toronto, Ontario, Canada", want_us=False, want_canada=True)

    def test_country_code_prefix_not_us(self):
        # "DE-Berlin" is Germany, not the Delaware state code
        assert not filters.region_ok("DE-Berlin-Trion", want_us=True, want_canada=False)

    def test_named_foreign_country_beats_state_code_lookalike(self):
        # "IN - Bangalore, India" is India, not Indiana
        assert not filters.is_united_states("IN - Bangalore, India")
        assert not filters.is_united_states("Munich, Germany")
        assert not filters.is_united_states("CA - Sydney, Australia")

    def test_explicit_us_token_wins_for_multi_country_strings(self):
        assert filters.is_united_states("New York, USA; Bangalore, India")

    def test_state_code_with_spaced_suffix_still_us(self):
        assert filters.is_united_states("Dallas, TX - Headquarters")

    def test_other_americas_are_not_us(self):
        assert not filters.is_united_states("Remote - Latin America")
        assert not filters.is_united_states("South America")
        # "North America" remains US-eligible (US-inclusive remote regions).
        assert filters.is_united_states("Remote (North America)")

    def test_canada_vetoes_state_code_lookalike(self):
        # The Magna leak: "Milton, Ontario, CA" read the trailing CA as
        # California. A province name / "Canada" beats a bare state code…
        assert not filters.is_united_states("Milton, Ontario, CA")
        assert not filters.is_united_states("Toronto, ON, Canada")
        # …but a full US state name still wins ("Ontario, California" is a
        # real US city), and explicit US tokens are untouched.
        assert filters.is_united_states("Ontario, California")
        assert filters.is_united_states("Ontario, California, United States")


class TestCategory:
    def test_categories(self):
        assert filters.categorize("Software Engineer Intern") == "Software"
        assert filters.categorize("Machine Learning Intern") == "Data & ML/AI"
        assert filters.categorize("Hardware Engineering Intern") == "Hardware"


class TestInferSeason:
    def test_inferred(self):
        assert filters.infer_season("Software Engineer Intern", None, CYCLES) == "2026 Graduates"

class TestSeasonFromText:
    def test_text(self):
        assert filters.season_from_text("We are looking for 2026 graduates to join as intern.") == "2026 Graduates"

