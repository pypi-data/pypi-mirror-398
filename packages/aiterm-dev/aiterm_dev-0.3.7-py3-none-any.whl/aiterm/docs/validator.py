"""Documentation validation for aiterm.

Provides validation of documentation files including:
- Broken link detection (internal and external)
- Code example testing
- Markdown syntax validation
- Cross-reference checking
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class LinkIssue:
    """Represents a broken or problematic link."""

    file: Path
    line: int
    link: str
    issue_type: str  # "broken_internal", "broken_external", "missing_anchor"
    message: str


@dataclass
class CodeExample:
    """Represents a code example in documentation."""

    file: Path
    language: str
    code: str
    line_start: int
    line_end: int


@dataclass
class ValidationResult:
    """Results from documentation validation."""

    total_files: int
    total_links: int
    total_examples: int
    link_issues: List[LinkIssue]
    example_failures: List[Dict[str, Any]]
    warnings: List[str]

    @property
    def has_issues(self) -> bool:
        """Check if any issues were found."""
        return len(self.link_issues) > 0 or len(self.example_failures) > 0

    @property
    def issue_count(self) -> int:
        """Total number of issues."""
        return len(self.link_issues) + len(self.example_failures)


class DocsValidator:
    """Validate documentation files for broken links and code examples."""

    # Default documentation directory
    DOCS_DIR = Path("docs/")

    # Link patterns
    MARKDOWN_LINK_PATTERN = r'\[([^\]]+)\]\(([^\)]+)\)'
    ANCHOR_PATTERN = r'#([a-zA-Z0-9_-]+)'

    def __init__(self, docs_dir: Optional[Path] = None, project_root: Optional[Path] = None):
        """Initialize documentation validator.

        Args:
            docs_dir: Path to documentation directory (defaults to ./docs)
            project_root: Path to project root (defaults to current directory)
        """
        self.docs_dir = docs_dir or self.DOCS_DIR
        self.project_root = project_root or Path.cwd()

        if not self.docs_dir.is_absolute():
            self.docs_dir = self.project_root / self.docs_dir

    def validate_links(self, check_external: bool = False) -> List[LinkIssue]:
        """Validate all links in documentation files.

        Args:
            check_external: Whether to check external URLs (slow)

        Returns:
            List of link issues found.
        """
        issues = []

        # Get all markdown files
        md_files = list(self.docs_dir.glob("**/*.md"))

        # Build set of valid internal files and anchors
        valid_files = self._get_valid_files(md_files)
        valid_anchors = self._get_valid_anchors(md_files)

        for md_file in md_files:
            content = md_file.read_text()
            lines = content.split('\n')

            # Find all links
            for line_num, line in enumerate(lines, start=1):
                for match in re.finditer(self.MARKDOWN_LINK_PATTERN, line):
                    link_text = match.group(1)
                    link_url = match.group(2)

                    # Skip mailto, tel, etc.
                    if link_url.startswith(('mailto:', 'tel:', 'javascript:')):
                        continue

                    # Check internal links
                    if not link_url.startswith(('http://', 'https://', '//')):
                        issue = self._validate_internal_link(
                            md_file, line_num, link_url, valid_files, valid_anchors
                        )
                        if issue:
                            issues.append(issue)

                    # Check external links if requested
                    elif check_external:
                        issue = self._validate_external_link(md_file, line_num, link_url)
                        if issue:
                            issues.append(issue)

        return issues

    def _get_valid_files(self, md_files: List[Path]) -> Set[str]:
        """Get set of valid internal file paths.

        Args:
            md_files: List of markdown files

        Returns:
            Set of valid relative file paths
        """
        valid = set()
        for md_file in md_files:
            # Add relative path from docs directory
            rel_path = md_file.relative_to(self.docs_dir)
            valid.add(str(rel_path))

            # Also add without .md extension (common shorthand)
            valid.add(str(rel_path.with_suffix('')))

        return valid

    def _get_valid_anchors(self, md_files: List[Path]) -> Dict[str, Set[str]]:
        """Get mapping of files to valid anchor IDs.

        Args:
            md_files: List of markdown files

        Returns:
            Dictionary mapping file paths to sets of anchor IDs
        """
        anchors = {}

        for md_file in md_files:
            rel_path = str(md_file.relative_to(self.docs_dir))
            file_anchors = set()

            content = md_file.read_text()

            # Find all headings and convert to anchor IDs
            for line in content.split('\n'):
                if line.startswith('#'):
                    # Extract heading text
                    heading = line.lstrip('#').strip()
                    # Convert to anchor ID (lowercase, replace spaces with hyphens)
                    anchor_id = heading.lower().replace(' ', '-')
                    # Remove special characters
                    anchor_id = re.sub(r'[^a-z0-9_-]', '', anchor_id)
                    file_anchors.add(anchor_id)

            anchors[rel_path] = file_anchors

        return anchors

    def _validate_internal_link(
        self,
        source_file: Path,
        line_num: int,
        link: str,
        valid_files: Set[str],
        valid_anchors: Dict[str, Set[str]]
    ) -> Optional[LinkIssue]:
        """Validate an internal link.

        Args:
            source_file: File containing the link
            line_num: Line number of the link
            link: Link URL
            valid_files: Set of valid file paths
            valid_anchors: Mapping of files to anchor IDs

        Returns:
            LinkIssue if problem found, None otherwise
        """
        # Split link into file and anchor
        if '#' in link:
            file_part, anchor = link.split('#', 1)
        else:
            file_part = link
            anchor = None

        # Resolve relative link
        if file_part:
            # Resolve relative to source file's directory
            source_dir = source_file.parent
            target_path = (source_dir / file_part).resolve()

            # Get relative path from docs directory
            try:
                rel_path = target_path.relative_to(self.docs_dir)
            except ValueError:
                # Link points outside docs directory
                return LinkIssue(
                    file=source_file,
                    line=line_num,
                    link=link,
                    issue_type="broken_internal",
                    message=f"Link points outside docs directory: {link}"
                )

            # Check if file exists
            if str(rel_path) not in valid_files and str(rel_path.with_suffix('')) not in valid_files:
                return LinkIssue(
                    file=source_file,
                    line=line_num,
                    link=link,
                    issue_type="broken_internal",
                    message=f"Target file not found: {rel_path}"
                )

            file_key = str(rel_path)
        else:
            # Link is just an anchor in the same file
            file_key = str(source_file.relative_to(self.docs_dir))

        # Check anchor if present
        if anchor:
            if file_key in valid_anchors:
                if anchor not in valid_anchors[file_key]:
                    return LinkIssue(
                        file=source_file,
                        line=line_num,
                        link=link,
                        issue_type="missing_anchor",
                        message=f"Anchor not found: #{anchor} in {file_key}"
                    )

        return None

    def _validate_external_link(
        self,
        source_file: Path,
        line_num: int,
        link: str
    ) -> Optional[LinkIssue]:
        """Validate an external link by checking HTTP status.

        Args:
            source_file: File containing the link
            line_num: Line number of the link
            link: Link URL

        Returns:
            LinkIssue if problem found, None otherwise
        """
        try:
            # Use curl for reliability (respects redirects, user-agent, etc.)
            result = subprocess.run(
                ['curl', '-I', '-s', '-o', '/dev/null', '-w', '%{http_code}', link],
                capture_output=True,
                text=True,
                timeout=10
            )

            status_code = result.stdout.strip()

            if status_code and status_code.startswith(('2', '3')):
                # 2xx or 3xx = OK
                return None
            else:
                return LinkIssue(
                    file=source_file,
                    line=line_num,
                    link=link,
                    issue_type="broken_external",
                    message=f"HTTP {status_code}: {link}"
                )

        except subprocess.TimeoutExpired:
            return LinkIssue(
                file=source_file,
                line=line_num,
                link=link,
                issue_type="broken_external",
                message=f"Timeout checking: {link}"
            )
        except Exception as e:
            return LinkIssue(
                file=source_file,
                line=line_num,
                link=link,
                issue_type="broken_external",
                message=f"Error checking: {str(e)}"
            )

    def extract_code_examples(self) -> List[CodeExample]:
        """Extract all code examples from documentation.

        Returns:
            List of code examples found.
        """
        examples = []

        md_files = list(self.docs_dir.glob("**/*.md"))

        for md_file in md_files:
            content = md_file.read_text()
            lines = content.split('\n')

            in_code_block = False
            code_language = None
            code_lines = []
            code_start = 0

            for line_num, line in enumerate(lines, start=1):
                # Check for code block start
                if line.startswith('```'):
                    if not in_code_block:
                        # Starting a code block
                        in_code_block = True
                        code_language = line[3:].strip() or 'text'
                        code_lines = []
                        code_start = line_num + 1
                    else:
                        # Ending a code block
                        in_code_block = False

                        # Create code example
                        if code_lines and code_language:
                            examples.append(CodeExample(
                                file=md_file,
                                language=code_language,
                                code='\n'.join(code_lines),
                                line_start=code_start,
                                line_end=line_num - 1
                            ))

                elif in_code_block:
                    code_lines.append(line)

        return examples

    def validate_code_examples(self, languages: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Validate code examples by attempting to parse/compile them.

        Args:
            languages: List of languages to validate (defaults to ['python', 'bash'])

        Returns:
            List of validation failures.
        """
        if languages is None:
            languages = ['python', 'bash']

        examples = self.extract_code_examples()
        failures = []

        for example in examples:
            if example.language.lower() not in languages:
                continue

            if example.language.lower() == 'python':
                failure = self._validate_python_code(example)
                if failure:
                    failures.append(failure)

            elif example.language.lower() in ('bash', 'sh', 'shell'):
                failure = self._validate_bash_code(example)
                if failure:
                    failures.append(failure)

        return failures

    def _validate_python_code(self, example: CodeExample) -> Optional[Dict[str, Any]]:
        """Validate Python code by attempting to compile it.

        Args:
            example: Code example to validate

        Returns:
            Failure dict if invalid, None if valid
        """
        try:
            compile(example.code, str(example.file), 'exec')
            return None
        except SyntaxError as e:
            return {
                'file': example.file,
                'language': example.language,
                'line_start': example.line_start,
                'line_end': example.line_end,
                'error': str(e),
                'error_type': 'SyntaxError',
                'code_snippet': example.code[:200]  # First 200 chars
            }

    def _validate_bash_code(self, example: CodeExample) -> Optional[Dict[str, Any]]:
        """Validate Bash code by checking syntax.

        Args:
            example: Code example to validate

        Returns:
            Failure dict if invalid, None if valid
        """
        try:
            # Use bash -n to check syntax without executing
            result = subprocess.run(
                ['bash', '-n'],
                input=example.code,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return {
                    'file': example.file,
                    'language': example.language,
                    'line_start': example.line_start,
                    'line_end': example.line_end,
                    'error': result.stderr,
                    'error_type': 'SyntaxError',
                    'code_snippet': example.code[:200]
                }

            return None

        except subprocess.TimeoutExpired:
            return {
                'file': example.file,
                'language': example.language,
                'line_start': example.line_start,
                'line_end': example.line_end,
                'error': 'Validation timeout',
                'error_type': 'Timeout',
                'code_snippet': example.code[:200]
            }
        except Exception as e:
            return {
                'file': example.file,
                'language': example.language,
                'line_start': example.line_start,
                'line_end': example.line_end,
                'error': str(e),
                'error_type': type(e).__name__,
                'code_snippet': example.code[:200]
            }

    def validate_all(self, check_external_links: bool = False) -> ValidationResult:
        """Run all validation checks.

        Args:
            check_external_links: Whether to check external URLs (slow)

        Returns:
            Validation results.
        """
        # Get all markdown files
        md_files = list(self.docs_dir.glob("**/*.md"))

        # Validate links
        link_issues = self.validate_links(check_external=check_external_links)

        # Extract and validate code examples
        examples = self.extract_code_examples()
        example_failures = self.validate_code_examples()

        # Collect warnings
        warnings = []
        if check_external_links:
            warnings.append("External link checking is slow and may have false positives")

        # Count total links
        total_links = 0
        for md_file in md_files:
            content = md_file.read_text()
            total_links += len(re.findall(self.MARKDOWN_LINK_PATTERN, content))

        return ValidationResult(
            total_files=len(md_files),
            total_links=total_links,
            total_examples=len(examples),
            link_issues=link_issues,
            example_failures=example_failures,
            warnings=warnings
        )
