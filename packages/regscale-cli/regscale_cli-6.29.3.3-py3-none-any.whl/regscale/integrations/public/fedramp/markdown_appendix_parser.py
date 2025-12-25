"""
This module provides a markdown-based parser for FedRAMP Appendix A documents.

The MarkdownAppendixParser uses pypandoc to convert DOCX files to markdown,
which properly handles content that spans page breaks in the original document.
This approach is more reliable than parsing Word XML directly because:
1. Pandoc normalizes the document structure
2. Page breaks are handled transparently
3. Tables split by page breaks are properly merged in the output
"""

import logging
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pypandoc

from regscale.integrations.public.fedramp.fedramp_common import CHECKBOX_CHARS

logger = logging.getLogger("regscale")

# Suppress pypandoc debug logging
logging.getLogger("pypandoc").setLevel(logging.WARNING)

# Control section markers
CONTROL_SUMMARY_MARKER = "Control Summary Information"
SOLUTION_MARKER = "What is the solution and how is it implemented?"

# Implementation statuses
STATUSES = [
    "Implemented",
    "Partially Implemented",
    "Planned",
    "In Remediation",
    "Inherited",
    "Alternative Implementation",
    "Not Applicable",
    "Archived",
    "Risk Accepted",
]

# Control originations
ORIGINATIONS = [
    "Service Provider Corporate",
    "Service Provider System Specific",
    "Service Provider Hybrid (Corporate and System Specific)",
    "Configured by Customer (Customer System Specific)",
    "Provided by Customer (Customer System Specific)",
    "Shared (Service Provider and Customer Responsibility)",
    "Inherited from pre-existing FedRAMP Authorization",
]

# Regex patterns - Control ID pattern for markdown tables (may have ** bold markers)
# Pattern to find "AC-2 Control Summary" or similar in tables
CONTROL_SUMMARY_PATTERN = re.compile(r"\*?\*?([A-Z]{2}-\d+(?:\(\d+\))?)\s+Control\s+Summary", re.IGNORECASE)
# Pattern to find control ID at start of section (e.g., "AC-2 Account Management")
CONTROL_SECTION_PATTERN = re.compile(r"^([A-Z]{2}-\d+(?:\(\d+\))?)\s+[A-Za-z]", re.MULTILINE)
# Use atomic patterns with negated character classes to avoid backtracking
PART_PATTERN = re.compile(r"Part\s+([a-z])\s*:", re.IGNORECASE)
# Parameter pattern: matches "Parameter AC-2(a): value" format with bounded lengths
PARAMETER_PATTERN = re.compile(r"Parameter\s([A-Z]{2}-\d{1,3}(?:\([a-z0-9]{1,5}\))?):\s?([^\n]{1,500})", re.IGNORECASE)


class MarkdownAppendixParser:
    """
    A parser for FedRAMP Appendix A documents that uses markdown conversion.

    This parser converts DOCX files to markdown using pypandoc, then extracts
    control implementation data from the resulting markdown tables. This approach
    handles page breaks gracefully because the markdown output properly merges
    content that was split across pages in the original document.
    """

    def __init__(self, filename: str):
        """
        Initialize the parser with a DOCX file.

        :param str filename: Path to the DOCX file to parse.
        """
        self.filename = filename
        self.markdown_content = ""
        self.controls_implementations: Dict[str, Dict] = {}
        self._convert_to_markdown()

    def _convert_to_markdown(self) -> None:
        """Convert the DOCX file to markdown using pypandoc."""
        try:
            self.markdown_content = pypandoc.convert_file(
                self.filename, "markdown", extra_args=["--wrap=none"]  # Prevent line wrapping in output
            )
            logger.debug("Successfully converted DOCX to markdown (%d characters)", len(self.markdown_content))
        except Exception as e:
            logger.error("Failed to convert DOCX to markdown: %s", e)
            raise

    def fetch_controls_implementations(self) -> Dict[str, Dict]:
        """
        Extract control implementations from the markdown content.

        :return: Dictionary mapping control IDs to their implementation data.
        :rtype: Dict[str, Dict]
        """
        self._parse_markdown_content()
        return self.controls_implementations

    def _parse_markdown_content(self) -> None:
        """Parse the markdown content to extract control implementations."""
        # Split content into control sections
        control_sections = self._split_into_control_sections()

        for control_id, section_content in control_sections.items():
            control_data = self._parse_control_section(section_content)
            if control_data:
                self.controls_implementations[control_id] = control_data

        logger.debug("Parsed %d controls from markdown", len(self.controls_implementations))

    def _split_into_control_sections(self) -> Dict[str, str]:
        """
        Split markdown content into sections by control ID.

        The markdown structure has:
        1. Control section headers like "AC-2 Account Management (L)(M)(H)"
        2. Control tables with "**AC-2 Control Summary Information**"

        :return: Dictionary mapping control IDs to their section content.
        :rtype: Dict[str, str]
        """
        sections = {}

        # Find all control summary sections using the table pattern
        # This is more reliable than section headers
        for match in CONTROL_SUMMARY_PATTERN.finditer(self.markdown_content):
            control_id = match.group(1)

            # Find the start of this control's content (look backward for section start)
            match_pos = match.start()
            section_start = self._find_section_start(match_pos)

            # Find the end of this control's content (next control or end of doc)
            section_end = self._find_section_end(match_pos)

            # Extract the section
            section_content = self.markdown_content[section_start:section_end]
            sections[control_id] = section_content

        logger.debug("Found %d control sections in markdown", len(sections))
        return sections

    def _find_section_start(self, summary_pos: int) -> int:
        """
        Find the start of a control section by looking backward from the summary table.

        :param int summary_pos: Position of the Control Summary table.
        :return: Start position of the section.
        :rtype: int
        """
        # Look backward for a control section header or previous table end
        search_text = self.markdown_content[:summary_pos]

        # Find the last control section pattern before this position
        last_section_match = None
        for match in CONTROL_SECTION_PATTERN.finditer(search_text):
            last_section_match = match

        if last_section_match:
            return last_section_match.start()

        # If no section header found, start from beginning or last table end
        return max(0, summary_pos - 5000)  # Reasonable lookback

    def _find_section_end(self, summary_pos: int) -> int:
        """
        Find the end of a control section.

        :param int summary_pos: Position of current Control Summary table.
        :return: End position of the section.
        :rtype: int
        """
        # Look for the next control summary table
        search_text = self.markdown_content[summary_pos + 50 :]

        next_match = CONTROL_SUMMARY_PATTERN.search(search_text)
        if next_match:
            # Also look for the section header of the next control
            section_match = CONTROL_SECTION_PATTERN.search(search_text)
            if section_match and section_match.start() < next_match.start():
                return summary_pos + 50 + section_match.start()
            return summary_pos + 50 + next_match.start()

        return len(self.markdown_content)

    def _parse_control_section(self, section: str) -> Optional[Dict]:
        """
        Parse a single control section to extract implementation data.

        :param str section: The section content.
        :return: Dictionary containing control implementation data.
        :rtype: Optional[Dict]
        """
        control_data: Dict = {}

        # Extract status
        status = self._extract_status(section)
        if status:
            control_data["status"] = status

        # Extract origination
        origination = self._extract_origination(section)
        if origination:
            control_data["origination"] = origination

        # Extract parameters
        parameters = self._extract_parameters(section)
        if parameters:
            control_data["parameters"] = parameters

        # Extract parts (implementation statements)
        parts = self._extract_parts(section)
        if parts:
            control_data["parts"] = parts

        # Extract responsibility
        responsibility = self._extract_responsibility(section)
        if responsibility:
            control_data["responsibility"] = responsibility

        return control_data if control_data else None

    def _extract_status(self, section: str) -> Optional[str]:
        """
        Extract implementation status from section.

        :param str section: The section content.
        :return: The implementation status.
        :rtype: Optional[str]
        """
        for status in STATUSES:
            # Look for checked status
            for char in CHECKBOX_CHARS:
                pattern = f"{char}\\s*{re.escape(status)}"
                if re.search(pattern, section, re.IGNORECASE):
                    return status
        return None

    def _extract_origination(self, section: str) -> Optional[str]:
        """
        Extract control origination from section.

        :param str section: The section content.
        :return: Comma-separated origination values.
        :rtype: Optional[str]
        """
        found_originations = []

        for origination in ORIGINATIONS:
            for char in CHECKBOX_CHARS:
                # Check for checked origination
                pattern = f"{char}\\s*{re.escape(origination)}"
                if re.search(pattern, section, re.IGNORECASE):
                    if origination not in found_originations:
                        found_originations.append(origination)
                    break

        return ",".join(found_originations) if found_originations else None

    def _extract_parameters(self, section: str) -> List[Dict[str, str]]:
        """
        Extract parameters from section.

        :param str section: The section content.
        :return: List of parameter dictionaries.
        :rtype: List[Dict[str, str]]
        """
        parameters = []
        for match in PARAMETER_PATTERN.finditer(section):
            param_name = match.group(1).strip()
            param_value = match.group(2).strip()
            parameters.append({"name": param_name, "value": param_value})
        return parameters

    def _extract_parts(self, section: str) -> List[Dict[str, str]]:
        """
        Extract implementation parts from section.

        This method finds the "What is the solution" section and extracts
        all parts (Part a, Part b, etc.) along with their content.
        Content that spans page breaks is properly merged.

        :param str section: The section content.
        :return: List of part dictionaries.
        :rtype: List[Dict[str, str]]
        """
        parts = []

        # Find the solution section
        solution_idx = section.lower().find("what is the solution")
        if solution_idx == -1:
            return parts

        solution_section = section[solution_idx:]

        # Extract content from markdown tables
        table_content = self._extract_table_content(solution_section)

        if not table_content:
            return parts

        # Parse parts from the combined table content
        parts = self._parse_parts_from_content(table_content)

        return parts

    def _extract_table_content(self, section: str) -> str:
        """
        Extract and merge content from markdown tables.

        This method handles tables that were split by page breaks by
        collecting all table content until a new control section starts.
        Preserves paragraph structure by using newlines as separators.

        :param str section: The section containing tables.
        :return: Combined table content with preserved formatting.
        :rtype: str
        """
        content_lines = []
        lines = section.split("\n")
        in_table = False
        current_paragraph = []

        for line in lines:
            # Check if we're in a table (pipe characters or table borders)
            if line.strip().startswith("|") or line.strip().startswith("+"):
                in_table = True
                # Extract content from table row
                content = self._extract_line_content(line)
                if content:
                    current_paragraph.append(content)
                elif current_paragraph:
                    # Empty content line - end of paragraph
                    content_lines.append(" ".join(current_paragraph))
                    current_paragraph = []
            elif in_table and not line.strip():
                # Empty line - preserve paragraph break
                if current_paragraph:
                    content_lines.append(" ".join(current_paragraph))
                    current_paragraph = []
            elif line.strip().startswith("="):
                # Table header separator
                pass

        # Don't forget last paragraph
        if current_paragraph:
            content_lines.append(" ".join(current_paragraph))

        # Join paragraphs with double newline to preserve structure
        return "\n\n".join(content_lines)

    def _extract_line_content(self, line: str) -> str:
        """
        Extract text content from a markdown table line.

        :param str line: A markdown table line.
        :return: Extracted text content.
        :rtype: str
        """
        # Remove table border characters
        content = line.strip()
        if content.startswith("|"):
            content = content[1:]
        if content.endswith("|"):
            content = content[:-1]
        if content.startswith("+") or content.endswith("+"):
            return ""
        if all(c in "-=+" for c in content):
            return ""

        # Clean up extra whitespace
        content = " ".join(content.split())
        return content.strip()

    def _parse_parts_from_content(self, content: str) -> List[Dict[str, str]]:
        """
        Parse part sections from combined content.

        :param str content: Combined table content.
        :return: List of part dictionaries.
        :rtype: List[Dict[str, str]]
        """
        parts = []

        # Find all part markers
        part_matches = list(PART_PATTERN.finditer(content))

        if not part_matches:
            # No explicit parts, treat as single part
            clean_content = self._clean_solution_content(content)
            if clean_content:
                parts.append({"name": "Default Part", "value": clean_content})
            return parts

        for i, match in enumerate(part_matches):
            part_letter = match.group(1).lower()
            part_name = f"Part {part_letter}"

            # Get content until next part or end
            start_idx = match.end()
            if i + 1 < len(part_matches):
                end_idx = part_matches[i + 1].start()
            else:
                end_idx = len(content)

            part_content = content[start_idx:end_idx].strip()
            part_content = self._clean_solution_content(part_content)

            if part_content:
                parts.append({"name": part_name, "value": part_content})

        return parts

    def _clean_solution_content(self, content: str) -> str:
        """
        Clean solution content by removing table artifacts while preserving formatting.

        :param str content: Raw content from table.
        :return: Cleaned content with preserved paragraph structure.
        :rtype: str
        """
        # Remove the "What is the solution" header if present
        content = re.sub(r"What is the solution and how is it implemented\??\s*", "", content, flags=re.IGNORECASE)

        # Remove table border artifacts
        content = re.sub(r"\+[-=]+\+", "", content)
        content = content.replace("|", "")

        # Remove markdown blockquote artifacts (> followed by optional whitespace and period)
        content = re.sub(r">\s*\.", "", content)
        # Remove standalone > characters (blockquote markers)
        content = re.sub(r"^\s*>\s*$", "", content, flags=re.MULTILINE)

        # Clean up each paragraph while preserving structure
        paragraphs = content.split("\n\n")
        cleaned_paragraphs = []
        for para in paragraphs:
            # Normalize whitespace within paragraph only
            cleaned = " ".join(para.split())
            if cleaned and cleaned.strip(": "):
                cleaned_paragraphs.append(cleaned.strip(": "))

        # Rejoin with double newlines to preserve paragraph breaks
        return "\n\n".join(cleaned_paragraphs)

    def _extract_responsibility(self, section: str) -> Optional[str]:
        """
        Extract responsible role from section.

        :param str section: The section content.
        :return: The responsible role.
        :rtype: Optional[str]
        """
        match = re.search(r"Responsible\s+Role[:\s]+([^\n|+]+)", section, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None


def _get_preferred_value(docx_data: Dict, md_data: Dict, key: str, prefer_docx: bool = True) -> Optional[str]:
    """
    Get the preferred value for a field from DOCX or markdown parser results.

    :param Dict docx_data: Data from DOCX parser.
    :param Dict md_data: Data from markdown parser.
    :param str key: The key to look up.
    :param bool prefer_docx: If True, prefer DOCX parser value; otherwise prefer markdown.
    :return: The preferred value or None.
    :rtype: Optional[str]
    """
    if prefer_docx:
        return docx_data.get(key) or md_data.get(key)
    return md_data.get(key) or docx_data.get(key)


def _build_statement_from_parts(parts: List[Dict[str, str]]) -> str:
    """
    Build a combined implementation statement from parts with HTML formatting.

    :param List[Dict[str, str]] parts: List of part dictionaries with 'name' and 'value'.
    :return: Combined statement with part labels and HTML formatting.
    :rtype: str
    """
    if not parts:
        return ""
    statement_parts = []
    for part in parts:
        name = part.get("name", "")
        value = part.get("value", "")
        if value:
            # Convert newlines to HTML paragraphs for proper formatting in RegScale
            # Double newlines become paragraph breaks, single newlines become line breaks
            formatted_value = value.replace("\n\n", "</p><p>").replace("\n", "<br/>")
            # Wrap in paragraph tags
            formatted_value = f"<p>{formatted_value}</p>"
            # Format as "Part a: content" with bold part label
            statement_parts.append(f"<p><strong>{name}:</strong></p>{formatted_value}")
    return "".join(statement_parts)


def _merge_single_control(docx_data: Dict, md_data: Dict) -> Dict:
    """
    Merge data for a single control from both parsers.

    :param Dict docx_data: Data from DOCX parser for this control.
    :param Dict md_data: Data from markdown parser for this control.
    :return: Merged control data.
    :rtype: Dict
    """
    merged_control: Dict = {}

    # Use DOCX parser for status, origination, parameters (better checkbox detection)
    for key in ("status", "origination", "parameters"):
        if value := _get_preferred_value(docx_data, md_data, key, prefer_docx=True):
            merged_control[key] = value

    # Use markdown parser for parts (handles page breaks better)
    # When we have markdown parts, build statement from them (full content)
    if md_data.get("parts"):
        merged_control["parts"] = md_data["parts"]
        # Build statement from parts - this contains the full page-spanning content
        merged_control["statement"] = _build_statement_from_parts(md_data["parts"])
    elif docx_data.get("parts"):
        merged_control["parts"] = docx_data["parts"]
        if docx_data.get("statement"):
            merged_control["statement"] = docx_data["statement"]

    # Only use statement if we don't have parts (fallback case)
    if "parts" not in merged_control:
        if value := _get_preferred_value(docx_data, md_data, "statement", prefer_docx=False):
            merged_control["statement"] = value

    # Use DOCX parser for responsibility
    if value := _get_preferred_value(docx_data, md_data, "responsibility", prefer_docx=True):
        merged_control["responsibility"] = value

    return merged_control


def merge_parser_results(docx_parser_results: Dict, md_parser_results: Dict) -> Dict:
    """
    Merge results from the DOCX parser and markdown parser.

    The DOCX parser is better at extracting checkbox states and statuses,
    while the markdown parser handles page-spanning content better.

    :param Dict docx_parser_results: Results from AppendixAParser.
    :param Dict md_parser_results: Results from MarkdownAppendixParser.
    :return: Merged results using best data from each parser.
    :rtype: Dict
    """
    merged = {}
    all_control_ids = set(docx_parser_results.keys()) | set(md_parser_results.keys())

    for control_id in all_control_ids:
        docx_data = docx_parser_results.get(control_id, {})
        md_data = md_parser_results.get(control_id, {})
        merged_control = _merge_single_control(docx_data, md_data)
        if merged_control:
            merged[control_id] = merged_control

    return merged
