#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SARIF Converter integration for RegScale CLI"""

import datetime
import logging
from typing import Optional

import click
from pathlib import Path

from regscale.core.app.utils.app_utils import (
    get_current_datetime,
)

logger = logging.getLogger("regscale")


@click.group()
def sarif() -> None:
    """Convert SARIF files to OCSF data using an API converter."""


@sarif.command(name="import")
@click.option(
    "--file_path",
    "-f",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path),
    help="Path to the SARIF file or a directory of files to convert",
    prompt="Enter the path",
    required=True,
)
@click.option(
    "--asset_id",
    "-id",
    type=click.INT,
    help="The RegScale Asset ID # to import the findings to.",
    prompt="RegScale Asset ID",
    required=True,
)
@click.option(
    "--scan_date",
    "-sd",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="The scan date of the file.",
    required=False,
    default=get_current_datetime("%Y-%m-%d"),
)
def import_sarif(file_path: Path, asset_id: int, scan_date: Optional[datetime.datetime] = None) -> None:
    """Convert a SARIF file(s) to OCSF format using an API converter."""
    process_sarif_files(file_path, asset_id, scan_date)


def process_sarif_files(file_path: Path, asset_id: int, scan_date: Optional[datetime.datetime]) -> None:
    """
    Process SARIF files for import.

    :param Path file_path: Path to the SARIF file or directory of files
    :param int asset_id: The RegScale Asset ID to import the findings to
    :param Optional[datetime.datetime] scan_date: The scan date of the file
    :return: None
    """
    from regscale.integrations.commercial.sarif.sarif_importer import SarifImporter

    if not scan_date:
        scan_date = get_current_datetime()
    SarifImporter(file_path, asset_id, scan_date=scan_date)
