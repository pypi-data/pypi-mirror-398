"""Tests for HTML export functionality.

These tests generate actual HTML files that can be viewed in a browser
for manual inspection. The HTML files are saved to tests/output/ and
are gitignored so they don't clutter the repository.

To view the generated HTML files:
    1. Run: pytest tests/test_export.py -v
    2. Serve: cd tests/output && python -m http.server 8000
    3. Open: http://localhost:8000 in your browser

Or open directly in browser:
    firefox tests/output/test_single_basic.html
"""

import json
import os
import re
import unittest
from pathlib import Path

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from django_mercury.export import export_html, export_summary_html
from tests.fixtures.sample_data import (
    create_failure_result,
    create_perfect_result,
    create_sample_monitor_result,
    create_sample_results_list,
    create_xss_test_result,
)

# Path to test output directory
TEST_OUTPUT_DIR = Path(__file__).parent / "output"


class TestHTMLExportSingle(unittest.TestCase):
    """Tests for single test HTML export."""

    def setUp(self):
        """Ensure output directory exists."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def test_single_export_creates_file(self):
        """Should create HTML file for single test result."""
        result = create_sample_monitor_result()
        output_path = TEST_OUTPUT_DIR / "test_single_basic.html"

        export_html(result, str(output_path))

        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 0)

    def test_single_with_n1_patterns(self):
        """Should render N+1 patterns in single test export."""
        result = create_sample_monitor_result(with_n1=True)
        output_path = TEST_OUTPUT_DIR / "test_single_with_n1.html"

        export_html(result, str(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Should contain N+1 pattern section
        self.assertIn("N+1", html)
        self.assertIn("SELECT * FROM posts WHERE user_id", html)

    def test_single_with_failures(self):
        """Should render failures in single test export."""
        result = create_failure_result()
        output_path = TEST_OUTPUT_DIR / "test_single_with_failures.html"

        export_html(result, str(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Should contain failure section
        self.assertIn("Failures", html)
        self.assertIn("Response time", html)

    def test_perfect_result(self):
        """Should render clean HTML for perfect test result."""
        result = create_perfect_result()
        output_path = TEST_OUTPUT_DIR / "test_single_perfect.html"

        export_html(result, str(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Should show pass status
        self.assertIn("PASSED", html)
        self.assertIn("status pass", html)


class TestHTMLExportSummary(unittest.TestCase):
    """Tests for multi-test summary HTML export."""

    def setUp(self):
        """Ensure output directory exists."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def test_summary_export_creates_file(self):
        """Should create HTML file for test summary."""
        results = create_sample_results_list(num_tests=10)
        output_path = TEST_OUTPUT_DIR / "test_summary_10_tests.html"

        export_summary_html(results, str(output_path))

        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 0)

    def test_summary_with_mixed_results(self):
        """Should render mixed pass/fail results correctly."""
        results = create_sample_results_list(num_tests=20, pass_rate=0.6, with_n1_rate=0.3)
        output_path = TEST_OUTPUT_DIR / "test_summary_mixed.html"

        export_summary_html(results, str(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Should contain stats
        self.assertIn("Total Tests", html)
        self.assertIn("Passed", html)
        self.assertIn("Failed", html)

    def test_empty_summary(self):
        """Should handle empty test results gracefully."""
        results = []
        output_path = TEST_OUTPUT_DIR / "test_summary_empty.html"

        export_summary_html(results, str(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn("No tests found", html)


@unittest.skipUnless(BS4_AVAILABLE, "beautifulsoup4 not installed")
class TestHTMLStructure(unittest.TestCase):
    """Tests for HTML structure and validity using BeautifulSoup."""

    def setUp(self):
        """Create sample HTML for parsing."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        results = create_sample_results_list(num_tests=10)
        self.output_path = TEST_OUTPUT_DIR / "test_structure.html"
        export_summary_html(results, str(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            self.html = f.read()
            self.soup = BeautifulSoup(self.html, "html.parser")

    def test_html_is_valid(self):
        """Should generate valid HTML document."""
        self.assertIsNotNone(self.soup.find("html"))
        self.assertIsNotNone(self.soup.find("head"))
        self.assertIsNotNone(self.soup.find("body"))
        self.assertIsNotNone(self.soup.find("title"))

    def test_has_viewport_meta(self):
        """Should include viewport meta tag for responsive design."""
        viewport = self.soup.find("meta", attrs={"name": "viewport"})
        self.assertIsNotNone(viewport)

    def test_has_charset_meta(self):
        """Should include UTF-8 charset declaration."""
        charset = self.soup.find("meta", attrs={"charset": "UTF-8"})
        self.assertIsNotNone(charset)

    def test_has_style_tag(self):
        """Should include inline CSS in style tag."""
        style = self.soup.find("style")
        self.assertIsNotNone(style)
        self.assertGreater(len(style.string), 100)


@unittest.skipUnless(BS4_AVAILABLE, "beautifulsoup4 not installed")
class TestDarkModeDesign(unittest.TestCase):
    """Tests for dark mode design requirements."""

    def setUp(self):
        """Create sample HTML for testing."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        results = create_sample_results_list(num_tests=5)
        self.output_path = TEST_OUTPUT_DIR / "test_dark_mode.html"
        export_summary_html(results, str(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            self.html = f.read()

    def test_dark_mode_colors_present(self):
        """Should use GitHub dark mode color palette."""
        # Check for key dark mode colors
        self.assertIn("#0d1117", self.html)  # Background
        self.assertIn("#161b22", self.html)  # Cards
        self.assertIn("#30363d", self.html)  # Borders
        self.assertIn("#c9d1d9", self.html)  # Text

    def test_no_emojis_in_html(self):
        """Should not contain any emoji characters."""
        # Unicode emoji ranges
        emoji_pattern = r"[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]"
        matches = re.findall(emoji_pattern, self.html)
        self.assertEqual(
            len(matches),
            0,
            f"Found {len(matches)} emoji characters: {matches[:5]}",
        )

    def test_no_gradients_in_css(self):
        """Should not use CSS gradients."""
        self.assertNotIn("linear-gradient", self.html.lower())
        self.assertNotIn("radial-gradient", self.html.lower())

    def test_professional_color_scheme(self):
        """Should use professional color scheme (no bright purple/pink)."""
        # Check that old gradient colors are NOT present
        self.assertNotIn("#667eea", self.html)  # Old purple
        self.assertNotIn("#764ba2", self.html)  # Old purple gradient


@unittest.skipUnless(BS4_AVAILABLE, "beautifulsoup4 not installed")
class TestSortableTables(unittest.TestCase):
    """Tests for sortable table functionality."""

    def setUp(self):
        """Create sample HTML with tables."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        results = create_sample_results_list(num_tests=10)
        self.output_path = TEST_OUTPUT_DIR / "test_tables.html"
        export_summary_html(results, str(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            self.html = f.read()
            self.soup = BeautifulSoup(self.html, "html.parser")

    def test_tables_have_sortable_class(self):
        """Should mark tables as sortable."""
        tables = self.soup.find_all("table", class_="sortable")
        self.assertGreater(len(tables), 0, "No sortable tables found")

    def test_table_headers_have_data_sort(self):
        """Should include data-sort attributes on th elements."""
        th_elements = self.soup.find_all("th", attrs={"data-sort": True})
        self.assertGreater(len(th_elements), 0, "No sortable headers found")

    def test_data_sort_types(self):
        """Should use correct data-sort types (string, number, date)."""
        th_elements = self.soup.find_all("th", attrs={"data-sort": True})

        sort_types = [th.get("data-sort") for th in th_elements]
        valid_types = {"string", "number", "date"}

        for sort_type in sort_types:
            self.assertIn(
                sort_type,
                valid_types,
                f"Invalid sort type: {sort_type}",
            )

    def test_table_has_tbody(self):
        """Should structure tables with thead and tbody."""
        tables = self.soup.find_all("table")
        for table in tables:
            tbody = table.find("tbody")
            self.assertIsNotNone(tbody, "Table missing tbody")


@unittest.skipUnless(BS4_AVAILABLE, "beautifulsoup4 not installed")
class TestJavaScriptIntegration(unittest.TestCase):
    """Tests for JavaScript module integration and data injection."""

    def setUp(self):
        """Create sample HTML for testing."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        results = create_sample_results_list(num_tests=10)
        self.output_path = TEST_OUTPUT_DIR / "test_javascript.html"
        export_summary_html(results, str(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            self.html = f.read()
            self.soup = BeautifulSoup(self.html, "html.parser")

    def test_canvas_elements_for_charts(self):
        """Should include canvas elements for Chart.js."""
        canvas_elements = self.soup.find_all("canvas")
        self.assertGreaterEqual(len(canvas_elements), 2, "Missing chart canvas elements")

        # Check for specific chart IDs
        response_chart = self.soup.find("canvas", id="responseTimeChart")
        self.assertIsNotNone(response_chart, "Missing responseTimeChart canvas")

        query_chart = self.soup.find("canvas", id="queryDistChart")
        self.assertIsNotNone(query_chart, "Missing queryDistChart canvas")

    def test_mercury_data_json_injected(self):
        """Should inject window.MERCURY_DATA with test data."""
        self.assertIn("window.MERCURY_DATA", self.html)

        # Extract JSON data
        match = re.search(r"window\.MERCURY_DATA\s*=\s*({[^;]+})", self.html)
        self.assertIsNotNone(match, "Could not find MERCURY_DATA JSON")

        json_str = match.group(1)
        data = json.loads(json_str)

        # Verify structure
        self.assertIn("tests", data)
        self.assertIn("stats", data)
        self.assertEqual(len(data["tests"]), 10)
        self.assertEqual(data["stats"]["total"], 10)

    def test_module_script_import(self):
        """Should have inline ES module with Chart.js import."""
        script = self.soup.find("script", attrs={"type": "module"})
        self.assertIsNotNone(script, "No module script found")

        # Should be inline (no src attribute)
        src = script.get("src")
        self.assertIsNone(src, "Script should be inline, not external")
        
        # Should contain Chart.js CDN import
        script_content = script.string or ""
        self.assertIn("import Chart from", script_content)
        self.assertIn("cdn.jsdelivr.net/npm/chart.js", script_content)

    def test_mercury_data_has_correct_fields(self):
        """Should include all required fields in MERCURY_DATA."""
        match = re.search(r"window\.MERCURY_DATA\s*=\s*({[^;]+})", self.html)
        data = json.loads(match.group(1))

        # Check test data structure
        test = data["tests"][0]
        self.assertIn("name", test)
        self.assertIn("response_time", test)
        self.assertIn("query_count", test)
        self.assertIn("status", test)
        self.assertIn("has_n1", test)

        # Check stats structure
        stats = data["stats"]
        self.assertIn("total", stats)
        self.assertIn("passed", stats)
        self.assertIn("failed", stats)
        self.assertIn("avg_time", stats)
        self.assertIn("avg_queries", stats)


@unittest.skipUnless(BS4_AVAILABLE, "beautifulsoup4 not installed")
class TestHTMLEscaping(unittest.TestCase):
    """Tests for proper HTML escaping of special characters."""

    def setUp(self):
        """Create HTML with XSS test data."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        result = create_xss_test_result()
        self.output_path = TEST_OUTPUT_DIR / "test_xss_escaping.html"
        export_html(result, str(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            self.html = f.read()
            self.soup = BeautifulSoup(self.html, "html.parser")

    def test_script_tags_escaped(self):
        """Should escape <script> tags in content."""
        # Raw <script> tags should not exist (except in our own JS)
        # Check that user-provided script tags are escaped
        self.assertIn("&lt;script&gt;", self.html)

    def test_html_entities_escaped(self):
        """Should escape HTML special characters."""
        self.assertIn("&amp;", self.html)  # & -> &amp;
        self.assertIn("&lt;", self.html)  # < -> &lt;
        self.assertIn("&gt;", self.html)  # > -> &gt;
        self.assertIn("&quot;", self.html)  # " -> &quot;

    def test_no_executable_scripts_in_content(self):
        """Should not allow executable JavaScript in user content."""
        # Count script tags
        script_tags = self.soup.find_all("script")

        # Should only have our legitimate scripts (module import and data injection)
        for script in script_tags:
            script_text = script.string or ""
            src = script.get("src", "")

            # Our legit scripts
            if "module" in script.get("type", ""):
                self.assertIn("main.mjs", src)
            elif "MERCURY_DATA" in script_text:
                # This is our data injection script
                pass
            else:
                self.fail(f"Unexpected script tag: {script}")


class TestTableDataAccuracy(unittest.TestCase):
    """Tests that table data matches input data."""

    def test_correct_number_of_rows(self):
        """Should have correct number of table rows matching input data."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        num_tests = 15
        results = create_sample_results_list(num_tests=num_tests)
        output_path = TEST_OUTPUT_DIR / "test_table_rows.html"

        export_summary_html(results, str(output_path))

        if not BS4_AVAILABLE:
            self.skipTest("beautifulsoup4 not installed")

        with open(output_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # Find "All Test Results" table
        all_tests_heading = soup.find("h2", string=re.compile(r"All Test Results"))
        self.assertIsNotNone(all_tests_heading)

        # Find table after this heading
        table = all_tests_heading.find_next("table")
        self.assertIsNotNone(table)

        # Count rows
        rows = table.find("tbody").find_all("tr")
        self.assertEqual(len(rows), num_tests)


if __name__ == "__main__":
    unittest.main()
