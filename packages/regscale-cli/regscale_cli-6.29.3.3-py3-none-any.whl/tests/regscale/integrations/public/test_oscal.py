#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test OSCAL Integrations"""

import json
import os
import sys
import tempfile
from typing import Tuple

import pytest

from regscale.core.app.utils.app_utils import check_file_path
from regscale.integrations.public.oscal import (
    process_component,
    process_fedramp_objectives,
    upload_catalog,
    upload_profile,
)
from regscale.utils.threading.threadhandler import create_threads, thread_assignment
from tests import CLITestFixture

sys.path.append("..")  # Adds higher directory to python modules path.


class TestOscal(CLITestFixture):
    """Oscal Test Class"""

    @pytest.fixture(autouse=True)
    def oscal_catalog(self):
        """Test OSCAL Catalog"""
        catalog_path = self.get_tests_dir("tests/test_data/NIST-800-53r4_catalog_MIN.json")
        with open(catalog_path.absolute(), "r", encoding="utf-8") as infile:
            data = json.load(infile)
        return data

    @pytest.fixture(autouse=True)
    def oscal_control(self, oscal_catalog):
        """Test OSCAL Control"""
        control = oscal_catalog["catalog"]["groups"][0]["controls"][0]
        return control

    @staticmethod
    @pytest.fixture(autouse=True)
    def sample_control():
        """
        Provides a sample security control for tests.

        :return: A sample security control
        :rtype: dict
        """
        return {"id": "ctrl-1"}

    @staticmethod
    @pytest.fixture(autouse=True)
    def sample_part_with_prose():
        """
        Provides a sample part with prose for tests.

        :return: A sample part with prose
        :rtype: dict
        """
        return {"id": "part-1", "prose": "Sample prose.", "name": "statement"}

    @staticmethod
    @pytest.fixture(autouse=True)
    def sample_part_with_nested_parts():
        """
        Provides a sample part with nested parts for tests.

        :return: A sample part with nested parts
        :rtype: dict
        """
        return {
            "id": "part-2",
            "name": "objective",
            "parts": [
                {"id": "part-2-1", "name": "item", "props": [{"prose": "nested-prop-value"}], "prose": "Nested prose."}
            ],
            "prose": "First prose.",
        }

    @staticmethod
    @pytest.fixture(autouse=True)
    def sample_part_deeply_nested():
        """
        Provides a sample part with deeply nested parts for tests.

        :return: A sample part with deeply nested parts
        :rtype: dict
        """
        return {
            "id": "part-3",
            "name": "objective",
            "prose": "First prose.",
            "parts": [
                {
                    "id": "part-3-1",
                    "name": "item",
                    "prose": "Second prose.",
                    "parts": [{"id": "part-3-1-1", "name": "objective", "prose": "Deeply nested prose."}],
                }
            ],
        }

    @staticmethod
    @pytest.fixture(autouse=True)
    def sample_part_with_super_deep_nested_parts():
        """
        Provides a sample part with super deep nested parts for tests.

        :return: A sample part with super deep nested parts
        :rtype: dict
        """
        return {
            "id": "part-4",
            "name": "objective",
            "prose": "First prose.",
            "parts": [
                {
                    "id": "part-2-1",
                    "name": "item",
                    "props": [{"value": "nested-prop-value"}],
                    "prose": "Second prose.",
                    "parts": [
                        {
                            "id": "part-3-1",
                            "name": "objective",
                            "prose": "Third prose.",
                            "parts": [
                                {
                                    "id": "part-3-1-1",
                                    "name": "item",
                                    "prose": "Fourth prose.",
                                    "parts": [
                                        {
                                            "id": "part-3-1-1-1",
                                            "name": "objective",
                                            "prose": "Fifth prose.",
                                            "parts": [
                                                {
                                                    "id": "part-3-1-1-1-1",
                                                    "name": "item",
                                                    "prose": "Sixth prose.",
                                                    "parts": [
                                                        {
                                                            "id": "part-3-1-1-1-1-1",
                                                            "name": "objective",
                                                            "prose": "Seventh prose.",
                                                            "parts": [
                                                                {
                                                                    "id": "part-3-1-1-1-1-1-1",
                                                                    "name": "item",
                                                                }
                                                            ],
                                                        },
                                                    ],
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ],
        }

    @staticmethod
    def test_no_prose_or_name(sample_control):
        part = {"id": "part-0"}
        objectives = []
        result = process_fedramp_objectives(part, "", objectives, sample_control)
        assert result == ""
        assert len(objectives) == 0

    @staticmethod
    def test_with_prose_only(sample_part_with_prose, sample_control):
        part = sample_part_with_prose
        objectives = []
        result = process_fedramp_objectives(part, "", objectives, sample_control)
        assert "Sample prose." in result
        assert len(objectives) == 1

    @staticmethod
    def test_with_name_item(sample_control):
        part = {"id": "part-1", "name": "item", "prose": "Item prose."}
        objectives = []
        result = process_fedramp_objectives(part, "", objectives, sample_control)
        assert "Item prose." in result
        assert len(objectives) == 1

    @staticmethod
    def test_with_nested_parts(sample_part_with_nested_parts, sample_control):
        part = sample_part_with_nested_parts
        objectives = []
        result = process_fedramp_objectives(part, "", objectives, sample_control)
        assert "First prose." in result
        assert len(objectives) == 1

    @staticmethod
    def test_with_deeply_nested_parts(sample_part_deeply_nested, sample_control):
        part = sample_part_deeply_nested
        objectives = []
        result = process_fedramp_objectives(part, "", objectives, sample_control)
        assert "First prose." in result
        assert len(objectives) == 1

    @staticmethod
    def test_with_multiple_nested_parts(
        sample_part_with_nested_parts,
        sample_part_deeply_nested,
        sample_control,
        sample_part_with_super_deep_nested_parts,
    ):
        part = {
            "id": "part-4",
            "name": "objective",
            "parts": [
                sample_part_with_nested_parts,
                sample_part_deeply_nested,
                sample_part_with_super_deep_nested_parts,
            ],
        }
        objectives = []
        result = process_fedramp_objectives(part, "", objectives, sample_control)
        assert len(objectives) == 3
        assert result == ""

    @staticmethod
    def test_no_parts(sample_control):
        part = {"id": "part-5", "name": "objective", "prose": "No parts prose."}
        objectives = []
        result = process_fedramp_objectives(part, "", objectives, sample_control)
        assert "No parts prose." in result
        assert len(objectives) == 1

    def test_create_catalog(self, oscal_catalog):
        """Test Catalog Code"""
        check_file_path("processing")
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        # change the catalog name to the name of the test run id
        data = oscal_catalog
        with open(tmp_file.name, "w", encoding="utf-8") as outfile:
            title = data["catalog"]["metadata"]["title"]
            data["catalog"]["metadata"]["title"] = title.replace("(TEST)", self.title_prefix)
            cat_name = data["catalog"]["metadata"]["title"]
            json.dump(data, outfile, indent=4)
        # Pass default argument to click function
        self.logger.debug(tmp_file.name)

        self.upload_catalog(tmp_file.name)
        # delete extra data after we are finished
        self.delete_catalog_items()
        # delete the catalog
        self.delete_inserted_catalog(cat_name)
        self.logger.debug(cat_name)
        tmp_file.close()
        os.remove(tmp_file.name)

    def test_create_profile(self):
        """Test Profile Code"""
        if not os.path.exists("processing"):
            os.mkdir("processing")
        # Need a runner to allow click to work with pytest
        test_file_path = self.get_tests_dir("tests") / "test_data/fedramp_high_profile.json"
        with open(test_file_path, "r", encoding="utf-8") as infile:
            data = json.load(infile)
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        with open(tmp_file.name, "w", encoding="utf-8") as outfile:
            json.dump(data, outfile, indent=4)
            self.logger.debug(outfile.name)
        # change the profile title to the name of the test run id
        with open(tmp_file.name, "r", encoding="utf-8") as infile:
            data = json.load(infile)
        with open(tmp_file.name, "w", encoding="utf-8") as outfile:
            title = data["profile"]["metadata"]["title"]
            data["profile"]["metadata"]["title"] = self.title_prefix + title
            prof_name = data["profile"]["metadata"]["title"]
            json.dump(data, outfile, indent=4)
        self.logger.debug(prof_name)
        # Pass default argument to click function

        self.upload_profile(file_name=test_file_path, title=prof_name)
        # delete extra data after we are finished
        self.delete_inserted_profile(prof_name)
        self.logger.debug(prof_name)
        tmp_file.close()
        os.remove(tmp_file.name)

    def test_create_component(self):
        """Test Component Code"""
        if not os.path.exists("processing"):
            os.mkdir("processing")
        component_file_path = self.get_tests_dir("tests") / "test_data/oscal_component.yaml"
        with open(component_file_path, "r", encoding="utf-8") as infile:
            data = infile.read()
        self.logger.debug(data)
        assert data
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(bytes(data, "utf-8"))
        tmp_file.close()
        os.rename(tmp_file.name, tmp_file.name + ".yaml")
        filename = tmp_file.name + ".yaml"
        process_component(filename)
        os.remove(filename)

    @staticmethod
    def upload_profile(file_name, title) -> None:
        """
        Upload the catalog

        :param str file_name: file path to the catalog to upload to RegScale
        :param str title: title of the catalog
        :rtype: None
        """
        from pathlib import Path

        upload_profile(title=title, catalog=84, categorization="Moderate", file_name=Path(file_name))

    @staticmethod
    def upload_catalog(file_name) -> None:
        """Upload the catalog"""
        upload_catalog(file_name=file_name)

    def delete_catalog_items(self):
        """testing out deleting items for a catalog for debugging"""
        # update api pool limits to max_thread count from init.yaml
        self.api.pool_connections = (
            self.config["maxThreads"]
            if self.config["maxThreads"] > self.api.pool_connections
            else self.api.pool_connections
        )
        self.api.pool_maxsize = (
            self.config["maxThreads"] if self.config["maxThreads"] > self.api.pool_maxsize else self.api.pool_maxsize
        )
        inserted_items: list[dict] = [
            {"file_name": "newParameters.json", "regscale_module": "controlParameters"},
            {
                "file_name": "newTests.json",
                "regscale_module": "controlTestPlans",
            },
            {
                "file_name": "newObjectives.json",
                "regscale_module": "controlObjectives",
            },
            {
                "file_name": "newControls.json",
                "regscale_module": "securitycontrols",
            },
        ]
        for file in inserted_items:
            with open(f".{os.sep}processing{os.sep}{file['file_name']}", "r", encoding="utf-8") as infile:
                data = json.load(infile)
            create_threads(
                process=self.delete_inserted_items,
                args=(
                    data,
                    file["regscale_module"],
                    self.app.config,
                    self.api,
                    self.logger,
                ),
                thread_count=len(data),
            )

    def delete_inserted_catalog(self, cat_name):
        """delete catalog"""
        from regscale.models.regscale_models import Catalog

        cat_found = False
        cats = Catalog.get_list()
        for cat in cats:
            if cat.title == cat_name:
                delete_this_cat = cat
                cat_found = True
                break
        assert cat_found is True
        self.logger.info(delete_this_cat.model_dump())  # noqa
        response = delete_this_cat.delete()
        assert response is True

    def delete_inserted_profile(self, prof_name):
        """delete profile"""
        from regscale.models.regscale_models import Profile

        profs = Profile.get_list()
        delete_this_prof = [prof for prof in profs if prof.name == prof_name][0]
        self.logger.info(delete_this_prof.model_dump())
        assert delete_this_prof is not None
        response = delete_this_prof.delete()
        assert response is True

    @staticmethod
    def delete_inserted_items(args: Tuple, thread: int) -> None:
        """
        Delete items that were added to the catalog
        :rtype: None
        """
        inserted_items, regscale_module, config, api, logger = args
        headers = {
            "accept": "*/*",
            "Authorization": config["token"],
        }
        # find which records should be executed by the current thread
        threads = thread_assignment(thread=thread, total_items=len(inserted_items))

        # iterate through the thread assignment items and process them
        for i in range(len(threads)):
            # set the recommendation for the thread for later use in the function
            item = inserted_items[threads[i]]

            url = f'{config["domain"]}/api/{regscale_module}/{item["id"]}'
            response = api.delete(url=url, headers=headers)
            if response.status_code == 200:
                logger.info("Deleted #%s from %s\n%s", item["id"], regscale_module, item)
            else:
                logger.error(
                    "Unable to delete #%s from %s\n%s",
                    item["id"],
                    regscale_module,
                    item,
                )

    @staticmethod
    def test_empty_part():
        part = {}
        str_obj = ""
        objectives = []
        ctrl = {}
        result = process_fedramp_objectives(part, str_obj, objectives, ctrl)
        assert result == ""

    @staticmethod
    def test_create_new_objective():
        part = {"name": "item", "prose": "This is a test objective", "id": "test_id"}
        str_obj = ""
        objectives = []
        ctrl = {"id": "test_ctrl_id"}
        _ = process_fedramp_objectives(part, str_obj, objectives, ctrl)
        assert len(objectives) == 1
        assert objectives[0]["name"] == "test_id"
        assert objectives[0]["part_id"] == "test_ctrl_id"

    @staticmethod
    def test_nested_control_parts(oscal_control):
        part = oscal_control["parts"][0]
        str_obj = ""
        objectives = []
        result = process_fedramp_objectives(part, str_obj, objectives, oscal_control)
        assert result == "The organization: "
        assert len(objectives) == 4
