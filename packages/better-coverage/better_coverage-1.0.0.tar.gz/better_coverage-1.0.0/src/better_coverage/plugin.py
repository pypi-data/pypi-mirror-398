"""Jest-style coverage reporter for pytest.

A pixel-perfect port of Istanbul's text reporter to Python, providing
Jest-compatible coverage output for pytest-cov.

This module implements:
- Tree-based coverage reporting (directories and files)
- Visitor pattern for tree traversal
- Terminal width-aware column truncation
- Color-coded output matching Istanbul's watermarks
- Support for branch coverage detection

Usage:
    Install the package:

        pip install better-coverage

    Then run pytest with coverage:

        pytest --cov=mypackage --cov-report=xml

    The Jest-style coverage table will print automatically after tests.

    The plugin is auto-discovered by pytest via entry points, no configuration needed.
"""

import os
import shutil
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest

NAME_COL: int = 4
PCT_COLS: int = 7
MISSING_COL: int = 17
TAB_SIZE: int = 1
DELIM: str = " | "


@dataclass
class MetricData:
    """Coverage metric data structure.

    Matches Istanbul's metric format: {total, covered, skipped, pct}

    Attributes:
        total: Total number of coverage points
        covered: Number of covered points
        skipped: Number of skipped points
        pct: Coverage percentage (0-100)
    """

    total: int
    covered: int
    skipped: int
    pct: float


@dataclass
class CoverageSummary:
    """Aggregated coverage summary.

    Matches Istanbul's CoverageSummary structure.

    Attributes:
        statements: Statement coverage metrics
        branches: Branch coverage metrics
        lines: Line coverage metrics
    """

    statements: MetricData
    branches: MetricData
    lines: MetricData

    def is_empty(self) -> bool:
        """Check if coverage data is empty."""
        return self.statements.total == 0


class CoverageNode:
    """Tree node representing a file or directory in the coverage hierarchy.

    Implements Istanbul's node protocol for visitor pattern traversal.

    Attributes:
        name: Node name (filename or directory name)
        parent: Parent node reference
        children: Dictionary of child nodes
        file_data: Coverage.py analysis data for files
        is_file: True if this is a file node, False for directories
    """

    def __init__(self, name: str, parent: Optional["CoverageNode"] = None) -> None:
        """Initialize coverage node.

        Args:
            name: Node name
            parent: Parent node (None for root)
        """
        self.name: str = name
        self.parent: Optional["CoverageNode"] = parent
        self.children: Dict[str, "CoverageNode"] = {}
        self.file_data: Optional[Tuple[str, List[int], List[int], List[int], str]] = None
        self.is_file: bool = False

    def get_relative_name(self) -> str:
        """Get a node's relative name.

        Returns:
            Node name, or 'All files' for root
        """
        return self.name if self.name else "All files"

    def is_summary(self) -> bool:
        """Check if this is a summary (directory) node.

        Returns:
            True for directories, False for files
        """
        return not self.is_file

    def get_parent(self) -> Optional["CoverageNode"]:
        """Get parent node.

        Returns:
            Parent node or None for root
        """
        return self.parent

    def get_coverage_summary(self) -> CoverageSummary:
        """Calculate a coverage summary for this node.

        For files, extracts metrics from coverage data.
        For directories, aggregates metrics from all children.

        Returns:
            Coverage summary with statement, branch, and line metrics
        """
        if self.is_file and self.file_data:
            fname, executed, excluded, missing, _ = self.file_data
            total: int = len(executed) + len(missing)
            covered: int = len(executed)
            pct: float = (covered / total * 100) if total > 0 else 100.0

            return CoverageSummary(
                statements=MetricData(total=total, covered=covered, skipped=0, pct=pct),
                branches=MetricData(total=0, covered=0, skipped=0, pct=0),
                lines=MetricData(total=total, covered=covered, skipped=0, pct=pct),
            )
        else:
            total_stmts: int = 0
            covered_stmts: int = 0
            total_lines: int = 0
            covered_lines: int = 0

            for child in self.children.values():
                summary: CoverageSummary = child.get_coverage_summary()
                total_stmts += summary.statements.total
                covered_stmts += summary.statements.covered
                total_lines += summary.lines.total
                covered_lines += summary.lines.covered

            stmt_pct: float = (covered_stmts / total_stmts * 100) if total_stmts > 0 else 0
            line_pct: float = (covered_lines / total_lines * 100) if total_lines > 0 else 0

            return CoverageSummary(
                statements=MetricData(total=total_stmts, covered=covered_stmts, skipped=0, pct=stmt_pct),
                branches=MetricData(total=0, covered=0, skipped=0, pct=0),
                lines=MetricData(total=total_lines, covered=covered_lines, skipped=0, pct=line_pct),
            )

    def get_file_coverage(self) -> Optional[Tuple[str, List[int], List[int], List[int], str]]:
        """Get raw file coverage data.

        Returns:
            Coverage.py analysis tuple for files, None for directories
        """
        return self.file_data

    def visit(self, visitor: Any) -> None:
        """Visit this node and all children using a visitor pattern.

        Calls visitor.on_summary() for directories and visitor.on_detail() for files.

        Args:
            visitor: Visitor object with on_summary() and on_detail() methods
        """
        if self.is_file:
            visitor.on_detail(self)
        else:
            visitor.on_summary(self)
            for child in sorted(self.children.values(), key=lambda n: n.name):
                child.visit(visitor)


def padding(num: int, ch: str = " ") -> str:
    """Generate padding string.

    Args:
        num: Number of characters
        ch: Character to use for padding

    Returns:
        String of repeated characters
    """
    return ch * num


def fill(text: Any, width: int, right: bool = False, tabs: int = 0) -> str:
    """Fill text to a specified width with padding.

    Matches Istanbul's fill() function exactly, including truncation logic.

    Args:
        text: Text to fill
        width: Target width
        right: If True, right-align text
        tabs: Number of tabs (TAB_SIZE spaces each) to indent

    Returns:
        Padded/truncated string
    """
    text = str(text)
    leading_spaces: int = tabs * TAB_SIZE
    remaining: int = width - leading_spaces
    leader: str = padding(leading_spaces)
    fmt_str: str = ""

    if remaining > 0:
        strlen: int = len(text)

        if remaining >= strlen:
            fill_str: str = padding(remaining - strlen)
        else:
            fill_str = "..."
            length: int = remaining - len(fill_str)
            text = text[strlen - length :]
            right = True

        fmt_str = fill_str + text if right else text + fill_str

    return leader + fmt_str


def format_name(name: str, max_cols: int, level: int) -> str:
    """Format filename with indentation.

    Args:
        name: Filename
        max_cols: Maximum column width
        level: Indentation level (0 for root)

    Returns:
        Formatted, indented name
    """
    return fill(name, max_cols, False, level)


def format_pct(pct: Any, width: int = PCT_COLS) -> str:
    """Format percentage value, right-aligned.

    Args:
        pct: Percentage value (number or string)
        width: Column width

    Returns:
        Formatted percentage string
    """
    return fill(pct, width, True, 0)


def node_missing(node: CoverageNode) -> str:  # noqa: C901
    """Calculate uncovered line ranges for a file.

    Matches Istanbul's nodeMissing() algorithm exactly.
    Returns empty string for directories.

    Args:
        node: Coverage node

    Returns:
        Comma-separated line ranges (e.g. "12-15,20,25-30")
    """
    if node.is_summary():
        return ""

    metrics: CoverageSummary = node.get_coverage_summary()
    if metrics.is_empty():
        return ""

    lines_pct: float = metrics.lines.pct
    file_data: Optional[Tuple[str, List[int], List[int], List[int], str]] = node.get_file_coverage()

    if not file_data:
        return ""

    fname, executed, excluded, missing, _ = file_data

    if lines_pct == 100:
        return ""

    if not missing:
        return ""

    missing_sorted = sorted(missing)

    new_range: bool = True
    acum: List[List[int]] = []

    for line_num in missing_sorted:
        line_num = int(line_num)
        if new_range:
            acum.append([line_num])
            new_range = False
        else:
            if line_num == acum[-1][-1] + 1:
                if len(acum[-1]) == 1:
                    acum[-1].append(line_num)
                else:
                    acum[-1][1] = line_num
            else:
                acum.append([line_num])

    ranges: List[Any] = []
    for range_item in acum:
        if len(range_item) == 1:
            ranges.append(range_item[0])
        else:
            ranges.append(f"{range_item[0]}-{range_item[1]}")

    return ",".join(str(r) for r in ranges)


def node_name(node: CoverageNode) -> str:
    """Get display name for node.

    Args:
        node: Coverage node

    Returns:
        Node name or 'All files' for root
    """
    return node.get_relative_name() or "All files"


def depth_for(node: CoverageNode) -> int:
    """Calculate node depth by counting parents.

    Args:
        node: Coverage node

    Returns:
        Depth level (0 for root)
    """
    ret: int = 0
    current: Optional[CoverageNode] = node.get_parent()
    while current:
        ret += 1
        current = current.get_parent()
    return ret


def null_depth_for(_: CoverageNode) -> int:
    """Return zero depth (used for missing line calculations).

    Args:
        _: Coverage node

    Returns:
        Always 0
    """
    return 0


def find_width(
    root: CoverageNode, node_extractor: Callable[[CoverageNode], str], depth_fn: Callable[[CoverageNode], int] = null_depth_for
) -> int:
    """Find the maximum width needed for a column by walking the tree.

    Args:
        root: Root node to start traversal
        node_extractor: Function to extract text from node
        depth_fn: Function to calculate indentation depth

    Returns:
        Maximum width needed
    """
    last: List[int] = [0]

    def compare_width(node: CoverageNode) -> None:
        last[0] = max(last[0], TAB_SIZE * depth_fn(node) + len(node_extractor(node)))

    class WidthVisitor:
        @staticmethod
        def on_summary(n: CoverageNode) -> None:
            compare_width(n)

        @staticmethod
        def on_detail(n: CoverageNode) -> None:
            compare_width(n)

    root.visit(WidthVisitor())
    return last[0]


def make_line(name_width: int, missing_width: int) -> str:
    """Create a horizontal separator line.

    Args:
        name_width: Width of name column
        missing_width: Width of uncovered lines column

    Returns:
        Separator line string
    """
    name: str = padding(name_width, "-")
    pct: str = padding(PCT_COLS, "-")
    elements: List[str] = [name, pct, padding(PCT_COLS + 1, "-"), pct, padding(missing_width, "-")]
    return DELIM.replace(" ", "-").join(elements) + "-"


def table_header(max_name_cols: int, missing_width: int) -> str:
    """Create a table header row.

    Args:
        max_name_cols: Width of name column
        missing_width: Width of uncovered lines column

    Returns:
        Header row string
    """
    elements: List[str] = [
        format_name("File", max_name_cols, 0),
        format_pct("% Stmts"),
        format_pct("% Branch", PCT_COLS + 1),
        format_pct("% Lines"),
        format_name("Uncovered Line #s", missing_width, 0),
    ]
    return DELIM.join(elements) + " "


def is_full(metrics: CoverageSummary) -> bool:
    """Check if coverage is 100%.

    Args:
        metrics: Coverage summary

    Returns:
        True if all metrics are 100%
    """
    return metrics.statements.pct == 100 and metrics.branches.pct == 100 and metrics.lines.pct == 100


def class_for_percent(value: float) -> str:
    """Determine color class for percentage value.

    Uses Istanbul's default watermarks: [50, 80]

    Args:
        value: Percentage value

    Returns:
        'high' (>= 80%), 'medium' (>= 50%), or 'low' (< 50%)
    """
    if value >= 80:
        return "high"
    elif value >= 50:
        return "medium"
    else:
        return "low"


def colorize(text: str, clazz: str) -> str:
    """Apply ANSI color codes to text.

    Args:
        text: Text to colorize
        clazz: Color class ('high', 'medium', 'low')

    Returns:
        Colorized text with ANSI codes
    """
    colors: Dict[str, str] = {
        "low": "\033[31m",
        "medium": "\033[33m",
        "high": "\033[32m",
    }
    reset: str = "\033[0m"

    if clazz in colors:
        return f"{colors[clazz]}{text}{reset}"
    return text


def table_row(
    node: CoverageNode,
    max_name_cols: int,
    level: int,
    skip_empty: bool,
    skip_full: bool,
    missing_width: int,
    has_branch_coverage: bool,
) -> str:
    """Create a table row for a node.

    Args:
        node: Coverage node
        max_name_cols: Width of name column
        level: Indentation level
        skip_empty: If True, skip empty files
        skip_full: If True, skip 100% covered files
        missing_width: Width of uncovered lines column
        has_branch_coverage: If True, show branch coverage; otherwise show '?'

    Returns:
        Formatted table row or empty string if skipped
    """
    name: str = node_name(node)
    metrics: CoverageSummary = node.get_coverage_summary()
    is_empty: bool = metrics.is_empty()

    if skip_empty and is_empty:
        return ""
    if skip_full and is_full(metrics):
        return ""

    mm: Dict[str, float] = {
        "statements": 0 if is_empty else metrics.statements.pct,
        "branches": 0 if is_empty else metrics.branches.pct,
        "lines": 0 if is_empty else metrics.lines.pct,
    }

    def colorize_cell(text: str, key: str) -> str:
        if is_empty:
            return text
        return colorize(text, class_for_percent(mm[key]))

    elements: List[str] = [
        colorize_cell(format_name(name, max_name_cols, level), "statements"),
        colorize_cell(format_pct(f"{mm['statements']:.2f}"), "statements"),
        colorize_cell(format_pct("?" if not has_branch_coverage else f"{mm['branches']:.2f}", PCT_COLS + 1), "branches"),
        colorize_cell(format_pct(f"{mm['lines']:.2f}"), "lines"),
        colorize(format_name(node_missing(node), missing_width, 0), "medium" if mm["lines"] == 100 else "low"),
    ]

    return DELIM.join(elements) + " "


class TextReport:
    """Istanbul-style text coverage report generator.

    Matches Istanbul's TextReport class behavior exactly.

    Attributes:
        max_cols: Maximum terminal width (0 = unlimited)
        skip_empty: Skip files with no coverage
        skip_full: Skip files with 100% coverage
        name_width: Calculated width for name column
        missing_width: Calculated width for uncovered lines column
        lines: Accumulated output lines
        has_branch_coverage: Whether branch coverage is available
    """

    def __init__(self, max_cols: Optional[int] = None, skip_empty: bool = False, skip_full: bool = False) -> None:
        """Initialize the text report.

        Args:
            max_cols: Maximum terminal width (None = auto-detect)
            skip_empty: Skip empty files
            skip_full: Skip 100% covered files
        """
        self.max_cols: int = max_cols if max_cols is not None else 120
        self.skip_empty: bool = skip_empty
        self.skip_full: bool = skip_full
        self.name_width: int = NAME_COL
        self.missing_width: int = MISSING_COL
        self.lines: List[str] = []
        self.has_branch_coverage: bool = False

    def on_start(self, root: CoverageNode) -> None:
        """Initialize report and print header.

        Calculates column widths and applies terminal width truncation.

        Args:
            root: Root coverage node
        """
        self.name_width = max(NAME_COL, find_width(root, node_name, depth_for))
        self.missing_width = max(MISSING_COL, find_width(root, node_missing))

        if self.max_cols > 0:
            pct_cols: int = len(DELIM) + 3 * (PCT_COLS + len(DELIM)) + 2

            max_remaining: int = self.max_cols - (pct_cols + MISSING_COL)
            if self.name_width > max_remaining:
                self.name_width = max_remaining
                self.missing_width = MISSING_COL
            elif self.name_width < max_remaining:
                max_remaining = self.max_cols - (self.name_width + pct_cols)
                if self.missing_width > max_remaining:
                    self.missing_width = max_remaining

        line: str = make_line(self.name_width, self.missing_width)
        self.lines.append(line)
        self.lines.append(table_header(self.name_width, self.missing_width))
        self.lines.append(line)

    def on_summary(self, node: CoverageNode) -> None:
        """Process directory node.

        Args:
            node: Directory node
        """
        node_depth: int = depth_for(node)
        row: str = table_row(
            node, self.name_width, node_depth, self.skip_empty, self.skip_full, self.missing_width, self.has_branch_coverage
        )
        if row:
            self.lines.append(row)

    def on_detail(self, node: CoverageNode) -> None:
        """Process file node.

        Args:
            node: File node
        """
        self.on_summary(node)

    def on_end(self) -> None:
        """Print footer line."""
        self.lines.append(make_line(self.name_width, self.missing_width))

    def execute(self, root: CoverageNode) -> str:
        """Generate the complete coverage report.

        Args:
            root: Root coverage node

        Returns:
            Complete report as string
        """
        self.on_start(root)
        root.visit(self)
        self.on_end()
        return "\n".join(self.lines)


def build_tree_from_coverage(cov: Any, base_dir: str) -> CoverageNode:
    """Build a coverage tree from coverage.py data.

    Args:
        cov: Coverage object
        base_dir: Base directory for relative paths

    Returns:
        Root coverage node
    """
    root: CoverageNode = CoverageNode("")

    data: Any = cov.get_data()
    files: List[str] = sorted(data.measured_files())

    for filename in files:
        if filename.startswith(base_dir):
            rel_path: str = filename[len(base_dir) :].lstrip("/")
        else:
            rel_path = filename

        parts: List[str] = rel_path.split("/")

        current: CoverageNode = root
        for i, part in enumerate(parts):
            if part not in current.children:
                current.children[part] = CoverageNode(part, current)
            current = current.children[part]

            if i == len(parts) - 1:
                current.is_file = True
                current.file_data = cov.analysis2(filename)

    return root


# noinspection PyUnusedLocal
@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter: Any, exitstatus: int, config: Any) -> None:
    """Pytest hook to print a Jest-style coverage report.

    Args:
        terminalreporter: Pytest terminal reporter
        exitstatus: Test exit status
        config: Pytest config object
    """
    if not config.pluginmanager.hasplugin("_cov"):
        return

    plugin: Any = config.pluginmanager.getplugin("_cov")

    if not hasattr(plugin, "cov_controller") or not plugin.cov_controller:
        return

    cov: Any = plugin.cov_controller.cov
    if not cov:
        return

    data: Any = cov.get_data()
    files: List[str] = sorted(data.measured_files())

    if not files:
        return

    base_dir: str = os.path.commonpath(files) if files else os.getcwd()

    root: CoverageNode = build_tree_from_coverage(cov, base_dir)

    try:
        max_cols: int = shutil.get_terminal_size().columns
    except (AttributeError, ValueError, OSError):
        max_cols = 120

    report: TextReport = TextReport(max_cols=max_cols)
    report.has_branch_coverage = data.has_arcs()

    output: str = report.execute(root)

    terminalreporter.write("\n")
    for line in output.split("\n"):
        terminalreporter.write_line(line)
