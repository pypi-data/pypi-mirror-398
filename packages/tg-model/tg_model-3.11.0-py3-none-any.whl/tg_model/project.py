# -*- coding: utf-8 -*-
# Copyright (C) 2023-2025 TUD | ZIH
# ralf.klammer@tu-dresden.de
# moritz.wilhelm@tu-dresden.de

import logging

from .collection import CollectionModeler
from .util import RenderBase
from .yaml import CollectionConfigTemplate, ProjectConfig


log = logging.getLogger(__name__)


class Project(RenderBase):

    def __init__(self, projectpath, templates=None, *args, **kw):
        super().__init__(projectpath, templates=templates)
        self.templates = templates
        self.collectors = []
        self._project_config = None
        self._avatar = None
        self._xslt = None
        self._requirements = None

    @property
    def requirements(self):
        if self._requirements is None:
            self._requirements = CollectionConfigTemplate(
                projectpath=self.projectpath
            ).extracted_requirements
        return self._requirements

    @property
    def project_config(self):
        if self._project_config is None:
            self._project_config = ProjectConfig(self.projectpath)
        return self._project_config

    def render_project(self, validate=True, export=True):

        for subproject in self.project_config.content["subprojects"]:
            collection = CollectionModeler(
                subproject, self.projectpath, templates=self.templates
            )
            if validate:
                collection.validate_collection(self.requirements)
            collection.render_collection()
            self.project_config.other_files.add_facets(collection.facets)
            if export:
                collection.export()
        self.project_config.other_files.render_all()

    def _validate_project(self):
        results = {"ok": [], "warning": [], "error": []}
        # Check if xslt, avatar and description are set
        if self.project_config.xslt:
            results["ok"].append("XSLT is set.")
        else:
            results["warning"].append("XSLT is not set.")

        if self.project_config.avatar:
            if self.project_config.avatar == "avatar.png":
                results["warning"].append("Avatar is set to default.")
            else:
                results["ok"].append("Avatar is set.")
        else:
            results["warning"].append("Avatar is not set.")

        if self.project_config.description:
            results["ok"].append("Description is set.")
        else:
            results["warning"].append("Description is not set.")

        # Check if at least one collector is set
        if not self.project_config.collectors:
            results["error"].append("No collectors are set.")
        else:
            results["ok"].append("At least one collector is set.")
            # Check if each collector has fullname and id/url
            for collector in self.project_config.collectors:
                if not collector.get("url"):
                    results["warning"].append(
                        f"Collector {collector['name']} has no URL defined!"
                    )
        return results

    def validate(self, file_attributes=False):
        # Structure to store validation results for the project
        # and its subprojects
        validation_results = {
            "project": None,
            "subprojects": [],
            # Flag to indicate if the project is ready for publication
            "ready_for_publication": True,
        }
        # General project validation
        validation_results["project"] = self._validate_project()
        # Validate each subproject
        for subproject in self.project_config.content["subprojects"]:
            collection = CollectionModeler(
                subproject, self.projectpath, templates=self.templates
            )
            sp_validation = collection.validate_collection(self.requirements)
            # Add validation results for this subproject
            _dict = {
                "subproject": subproject,
                "files": sp_validation["files"],
                "stats": sp_validation["stats"],
                "title": subproject["name"],
            }
            if file_attributes:
                _dict["file_attributes"] = collection.get_file_attributes()
            validation_results["subprojects"].append(_dict)
            # Check if there are errors in the subproject validation
            if sp_validation["stats"]["error"] > 0:
                validation_results["ready_for_publication"] = False

        return validation_results

    def export(self):

        for subproject in self.project_config.content["subprojects"]:
            collection = CollectionModeler(
                subproject, self.projectpath, templates=self.templates
            )
            collection.export()
