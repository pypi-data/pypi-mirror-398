"""
This module contains the MDDocParser class, which is used to parse an SSP Appendix A file
and return a dictionary representing the data in the markdown document.
"""

import logging
import re
from collections import defaultdict
from typing import Dict, TextIO, Optional, List

import pypandoc

from regscale.models import ProfileMapping

logger = logging.getLogger("regscale")

# Tokens used in HTML parsing
BEGINPARTTOKEN = "<tr>"
ENDPARTTOKEN = "</tr>"
BODYSTARTTOKEN = "<tbody>"
BODYENDTOKEN = "</tbody>"
CONTROLSUMMARYTOKEN = "What is the solution"

FULL_SUMMARY_TOKEN = "What is the solution and how is it implemented?"
html_tag_pattern = re.compile(r"</?[^>]+>")


def clean_part(part: str) -> str:
    """
    Cleans an HTML part string by removing specific HTML tags.

    :param part: The HTML part string
    :return: A cleaned HTML part string with specific tags removed
    """
    # Pattern to match specified HTML tags, using non-capturing groups for better performance
    pattern = re.compile(r"</?(td|tr|th|tbody|thead)(?: [^>]*)?>", re.IGNORECASE)
    return pattern.sub("", part).strip()


class MDDocParser:
    """
    Parses an SSP .md file and extracts control parts into a dictionary.
    """

    def __init__(self, md_path: str, profile_id: int):
        """
        Initializes the MDDocParser with the path to the markdown file.

        :param str md_path: Path to the markdown file
        :param int profile_id: The profile ID to associate with the control parts
        """
        # List of controls to parse
        self.md_path = md_path
        try:
            self.controls = [profile_map.controlId for profile_map in ProfileMapping.get_by_profile(profile_id)]
            # Convert .md file to markdown_strict format and save output
            self.md_text = pypandoc.convert_file(md_path, "markdown_strict", outputfile="app_a.md")
            self.md_doc = "app_a.md"
        except Exception as e:
            logger.error(f"Error converting file: {e}")
            raise

    def get_parts(self) -> Dict[str, str]:
        """
        Parses the .md file and extracts control parts.

        :return: A dictionary of control parts, keyed by control ID
        """
        control_parts_dict = defaultdict(str)
        try:
            with open(self.md_doc, "r") as file:
                for line in file:
                    if CONTROLSUMMARYTOKEN in line:
                        control_id = self._handle_control_summary_line(line)
                        if not control_id:
                            continue
                        # Skip lines to find the table content
                        next(file)  # Skip HTML table definition line
                        # Loop through file to capture parts between tbody tags
                        self.find_parts(file, control_parts_dict, control_id)
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
        return control_parts_dict

    @staticmethod
    def clean_html_and_newlines(input_text: str) -> str:
        """
        Cleans HTML tags and newlines from a string.
        :param str input_text: The text to clean
        :return: The cleaned text
        :rtype: str
        """
        # Remove HTML tags
        cleaner_text = html_tag_pattern.sub("", input_text)
        # Remove newlines
        return cleaner_text.replace("\n", "")

    def _handle_control_summary_line(self, line: str) -> Optional[str]:
        """
        Handles a line of text from the markdown file.

        :param str line: The line of text
        :return: The control ID
        :rtype: Optional[str]
        """
        # Extract control ID and clean it
        html_free_line = self.clean_html_and_newlines(line)
        # Use regex to find "what" case-insensitively and split
        pattern = re.compile(r"what", re.IGNORECASE)
        if pattern.search(html_free_line):
            clean_line = pattern.split(html_free_line)[0].strip()
        else:
            clean_line = html_free_line
        if not clean_line:
            return None
        clean_control_id_from_line = clean_line.strip()
        return clean_control_id_from_line

    @staticmethod
    def _is_section_boundary(line: str) -> bool:
        """
        Check if a line represents a section boundary (not a table continuation).

        :param str line: The line to check.
        :return: True if this is a section boundary.
        :rtype: bool
        """
        lower_line = line.lower()
        return "<table" not in lower_line and "<tbody" not in lower_line

    @staticmethod
    def _should_stop_parsing(in_tbody: bool, line: str) -> bool:
        """
        Determine if we should stop parsing based on current state and line content.

        :param bool in_tbody: Whether we're currently inside a tbody section.
        :param str line: The current line.
        :return: True if we should stop parsing.
        :rtype: bool
        """
        if in_tbody:
            return False
        if not line.strip():
            return False
        if BODYSTARTTOKEN in line:
            return False
        return MarkdownParser._is_section_boundary(line)

    def find_parts(self, file: TextIO, control_parts_dict: Dict, cntrlid: str):
        """
        Parses and collects parts from a markdown file into a dictionary by control ID.

        This method handles content that spans multiple table rows (which may represent
        page breaks in the original document) by collecting all content within tbody tags.

        :param file: The markdown file
        :param control_parts_dict: Dictionary to store parts by control ID
        :param cntrlid: The control ID
        """
        all_parts: List[str] = []
        in_tbody = False
        tbody_count = 0

        for line in file:
            if BODYSTARTTOKEN in line:
                in_tbody = True
                tbody_count += 1
                continue
            if BODYENDTOKEN in line:
                in_tbody = False
                continue

            if self._should_stop_parsing(in_tbody, line):
                break

            if in_tbody or BEGINPARTTOKEN in line:
                part_text = self.part_cleaner(file, line)
                if part_text.strip():
                    all_parts.append(part_text)

        allparts = " ".join(all_parts)

        if tbody_count > 1:
            logger.debug(
                "Control %s: Found %d tbody sections (possible page breaks), all content collected",
                cntrlid,
                tbody_count,
            )

        control_parts_dict[cntrlid] = allparts
        logger.debug("Control ID: %s, Parts length: %d chars", cntrlid, len(allparts))

    @staticmethod
    def part_cleaner(file: TextIO, line: str) -> str:
        """
        Cleans and accumulates parts of text from the markdown file.

        This method collects all text between table row markers, handling multi-line
        content that may have been split due to page breaks in the original document.

        :param file: The markdown file
        :param line: The current line of text
        :return: The cleaned part as a string
        """
        part_lines: List[str] = []

        # Clean and add the initial line if it has content
        initial_cleaned = clean_part(line)
        if initial_cleaned:
            part_lines.append(initial_cleaned)

        for next_line in file:
            cleaned_line = clean_part(next_line)
            if cleaned_line:
                part_lines.append(cleaned_line)
            if ENDPARTTOKEN in next_line:
                break

        # Join with space, preserving the text flow
        return " ".join(part_lines)
