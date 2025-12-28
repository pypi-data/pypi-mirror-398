"""Tests for better_coverage plugin."""

from better_coverage.plugin import (
    CoverageNode,
    CoverageSummary,
    MetricData,
    fill,
    format_name,
    format_pct,
    make_line,
    node_missing,
    padding,
    table_header,
)


class TestPadding:
    """Test padding function."""

    def test_padding_with_spaces(self) -> None:
        """Test padding generates correct number of spaces."""
        assert padding(5) == "     "
        assert padding(0) == ""
        assert padding(1) == " "

    def test_padding_with_custom_char(self) -> None:
        """Test padding with custom character."""
        assert padding(3, "-") == "---"
        assert padding(5, "*") == "*****"


class TestFill:
    """Test fill function."""

    def test_fill_with_enough_space(self) -> None:
        """Test fill when text fits in width."""
        result = fill("hello", 10, False, 0)
        assert len(result) == 10
        assert result == "hello     "

    def test_fill_right_aligned(self) -> None:
        """Test fill with right alignment."""
        result = fill("hello", 10, True, 0)
        assert len(result) == 10
        assert result == "     hello"

    def test_fill_with_truncation(self) -> None:
        """Test fill truncates long text."""
        result = fill("hello world test", 10, False, 0)
        assert len(result) == 10
        assert result == "...ld test"

    def test_fill_with_tabs(self) -> None:
        """Test fill with tab indentation."""
        result = fill("hello", 10, False, 2)
        assert result.startswith("  ")
        assert len(result) == 10


class TestFormatName:
    """Test format_name function."""

    def test_format_name_basic(self) -> None:
        """Test basic filename formatting."""
        result = format_name("test.py", 20, 0)
        assert "test.py" in result
        assert len(result) == 20

    def test_format_name_with_indentation(self) -> None:
        """Test filename with indentation level."""
        result = format_name("test.py", 20, 1)
        assert result.startswith(" ")


class TestFormatPct:
    """Test format_pct function."""

    def test_format_pct_basic(self) -> None:
        """Test percentage formatting."""
        result = format_pct("85.50")
        assert "85.50" in result
        assert len(result) == 7

    def test_format_pct_right_aligned(self) -> None:
        """Test percentage is right-aligned."""
        result = format_pct("5.0")
        assert result.endswith("5.0")


class TestNodeMissing:
    """Test node_missing function."""

    def test_node_missing_directory(self) -> None:
        """Test returns an empty string for directories."""
        node = CoverageNode("dir")
        node.is_file = False
        assert node_missing(node) == ""

    def test_node_missing_empty_file(self) -> None:
        """Test returns empty string for empty files."""
        node = CoverageNode("test.py")
        node.is_file = True
        node.file_data = ("test.py", [], [], [], "")
        assert node_missing(node) == ""

    def test_node_missing_full_coverage(self) -> None:
        """Test returns an empty string for 100% coverage."""
        node = CoverageNode("test.py")
        node.is_file = True
        node.file_data = ("test.py", [1, 2, 3, 4, 5], [], [], "")
        assert node_missing(node) == ""

    def test_node_missing_single_line(self) -> None:
        """Test a single missing line."""
        node = CoverageNode("test.py")
        node.is_file = True
        node.file_data = ("test.py", [1, 2, 4, 5], [], [3], "")
        result = node_missing(node)
        assert result == "3"

    def test_node_missing_consecutive_lines(self) -> None:
        """Test consecutive missing lines become range."""
        node = CoverageNode("test.py")
        node.is_file = True
        node.file_data = ("test.py", [1, 2, 8, 9], [], [3, 4, 5, 6, 7], "")
        result = node_missing(node)
        assert result == "3-7"

    def test_node_missing_multiple_ranges(self) -> None:
        """Test multiple ranges separated by commas."""
        node = CoverageNode("test.py")
        node.is_file = True
        node.file_data = ("test.py", [1, 5, 6, 10], [], [2, 3, 4, 7, 8, 9], "")
        result = node_missing(node)
        assert result == "2-4,7-9"

    def test_node_missing_mixed_ranges_and_singles(self) -> None:
        """Test a mix of ranges and single lines."""
        node = CoverageNode("test.py")
        node.is_file = True
        node.file_data = ("test.py", [1, 3, 5, 9], [], [2, 4, 6, 7, 8], "")
        result = node_missing(node)
        assert result == "2,4,6-8"


class TestCoverageNode:
    """Test CoverageNode class."""

    def test_node_creation(self) -> None:
        """Test node creation."""
        node = CoverageNode("test.py")
        assert node.name == "test.py"
        assert node.parent is None
        assert not node.is_file

    def test_node_with_parent(self) -> None:
        """Test node with parent."""
        parent = CoverageNode("src")
        child = CoverageNode("test.py", parent)
        assert child.parent == parent
        assert child.get_parent() == parent

    def test_get_relative_name(self) -> None:
        """Test get_relative_name."""
        node = CoverageNode("test.py")
        assert node.get_relative_name() == "test.py"

        root = CoverageNode("")
        assert root.get_relative_name() == "All files"

    def test_is_summary(self) -> None:
        """Test is_summary for directories and files."""
        dir_node = CoverageNode("src")
        assert dir_node.is_summary()

        file_node = CoverageNode("test.py")
        file_node.is_file = True
        assert not file_node.is_summary()

    def test_get_coverage_summary_for_file(self) -> None:
        """Test coverage summary calculation for files."""
        node = CoverageNode("test.py")
        node.is_file = True
        node.file_data = ("test.py", [1, 2, 3], [], [4, 5], "")

        summary = node.get_coverage_summary()
        assert summary.statements.total == 5
        assert summary.statements.covered == 3
        assert summary.statements.pct == 60.0

    def test_get_coverage_summary_aggregates_children(self) -> None:
        """Test coverage summary aggregates from children."""
        root = CoverageNode("src")

        child1 = CoverageNode("test1.py", root)
        child1.is_file = True
        child1.file_data = ("test1.py", [1, 2], [], [3], "")

        child2 = CoverageNode("test2.py", root)
        child2.is_file = True
        child2.file_data = ("test2.py", [1, 2, 3], [], [4, 5], "")

        root.children = {"test1.py": child1, "test2.py": child2}

        summary = root.get_coverage_summary()
        assert summary.statements.total == 8
        assert summary.statements.covered == 5
        assert summary.statements.pct == 62.5


class TestMakeLine:
    """Test make_line function."""

    def test_make_line_basic(self) -> None:
        """Test separator line generation."""
        line = make_line(40, 20)
        assert "-" in line
        assert "|" in line
        assert len(line) > 0


class TestTableHeader:
    """Test table_header function."""

    def test_table_header_basic(self) -> None:
        """Test header row generation."""
        header = table_header(40, 20)
        assert "File" in header
        assert "% Stmts" in header
        assert "% Branch" in header
        assert "% Lines" in header
        assert "Uncovered Line #s" in header
        assert "|" in header


class TestCoverageSummary:
    """Test CoverageSummary class."""

    def test_is_empty_true(self) -> None:
        """Test is_empty returns True for empty coverage."""
        summary = CoverageSummary(
            statements=MetricData(total=0, covered=0, skipped=0, pct=0),
            branches=MetricData(total=0, covered=0, skipped=0, pct=0),
            lines=MetricData(total=0, covered=0, skipped=0, pct=0),
        )
        assert summary.is_empty()

    def test_is_empty_false(self) -> None:
        """Test is_empty returns False for non-empty coverage."""
        summary = CoverageSummary(
            statements=MetricData(total=10, covered=5, skipped=0, pct=50),
            branches=MetricData(total=0, covered=0, skipped=0, pct=0),
            lines=MetricData(total=10, covered=5, skipped=0, pct=50),
        )
        assert not summary.is_empty()
