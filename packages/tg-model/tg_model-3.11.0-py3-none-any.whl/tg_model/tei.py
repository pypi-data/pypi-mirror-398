# -*- coding: utf-8 -*-
# Copyright (C) 2023-2025 TUD | ZIH
# ralf.klammer@tu-dresden.de

import logging
import os

from datetime import datetime
from iso639 import Lang  # type: ignore
from iso639.exceptions import InvalidLanguageValue  # type: ignore
from mimetypes import guess_type

from .util import (
    strip_strings_in_dict,
)

from .util_eltec import gender_to_authorgender, wordcount_to_size
from .validation import ValidationCollectionConfig
from .xml import XMLParserBase
from .yaml import CollectionConfig

log = logging.getLogger(__name__)


class TEIParser(XMLParserBase):
    def __init__(
        self,
        tree=None,
        path=None,
        filename=None,
        fullpath=None,
        *args,
        **kw,
    ):
        if tree is not None:
            super().__init__(tree=tree, *args, **kw)
        elif fullpath:
            super().__init__(fullpath, *args, **kw)
            self.fullpath = fullpath
        elif all([path, filename]):
            self.path = path
            self.filename = filename
            self.fullpath = os.path.join(path, filename)
            super().__init__(os.path.join(path, filename), *args, **kw)
        else:
            raise ValueError("TEIParser incorrect initialized")

        self._pure_filename = None
        self._publication = None
        self._pub_place = None
        self._edtion_pub_place = None
        self._pub_date_edition = None
        self._author = None
        self._author_id = None
        self._edition_author_fullname = None
        self._edition_author_firstname = None
        self._edition_author_lastname = None
        self._edition_author_id = None
        self._author_firstname = None
        self._author_lastname = None
        self._author_fullname = None
        self._work_id = None
        self._work_date = None
        self._work_notBefore = None
        self._work_notAfter = None
        self._work_title = None
        self._edition_title = None
        self._edition_license_url = None
        self._edition_license_title = None
        self._language = None
        self._genre = None
        self._wordcount = None
        self._eltec_time_slot = None
        self._eltec_author_gender = None
        self._eltec_size = None
        self._eltec_reprint_count = None
        self._eltec_corpus_collection = None
        self._rights_holder = None
        self._rights_holder_url = None
        self._rights_holder_fullname = None
        self._collector = None
        self._collector_url = None
        self._collector_fullname = None
        self._attributes = None
        self._basic_classifications = None
        self._gnd_subjects = None
        self._images = None

    def __repr__(self):
        return "<TEIParser: %s>" % self.uri

    def _get_via_config_value(self, config_val, multiple=False):
        if config_val:
            # First check xpath
            xpath = config_val.get("xpath")
            if xpath:
                result = self.findall(xpath) if multiple else self.find(xpath)
                if result:  # If xpath returns results
                    return result

            # Fallback to direct value
            direct_value = config_val.get("value")
            if direct_value is not None:
                return [direct_value] if multiple else direct_value

        # If neither xpath nor value is set, return None OR empty list
        return [] if multiple else None

    def get_via_config_value(self, value, section, multiple=False):
        config_val = section.get(value, None)
        return self._get_via_config_value(config_val, multiple=multiple)

    def set_config(self, config):
        self._config = config

    @property
    def config(self):
        if self._config is None:
            self.set_config(CollectionConfig())
        return self._config

    @property
    def pure_filename(self):
        if self.filename and self._pure_filename is None:
            self._pure_filename = self.filename.replace(".xml", "")
        return self._pure_filename

    @property
    def work_date(self):
        if self._work_date is None:
            self._work_date = self.get_via_config_value(
                "date", self.config.work["dateOfCreation"]
            )
            # if self._work_date and not is_valid_date(self._work_date):
            #     self._work_date = False
        return self._work_date

    @property
    def work_notBefore(self):
        if self._work_notBefore is None:
            self._work_notBefore = self.get_via_config_value(
                "notBefore", self.config.work["dateOfCreation"]
            )
        return self._work_notBefore

    @property
    def work_notAfter(self):
        if self._work_notAfter is None:
            self._work_notAfter = self.get_via_config_value(
                "notAfter", self.config.work["dateOfCreation"]
            )
        return self._work_notAfter

    def _get_date_range(self, notBefore, notAfter):
        return {
            "notBefore": notBefore,
            "notAfter": notAfter,
            "text": f"between {notBefore} and {notAfter}",
        }

    @property
    def work_dateRange(self):
        if all([self.work_notBefore, self.work_notAfter]):
            return self._get_date_range(
                self.work_notBefore, self.work_notAfter
            )

    @property
    def work_dateDefault(self):
        return self._get_date_range(-4000, datetime.now().strftime("%Y-%m-%d"))

    @property
    def pub_place(self):
        if self._pub_place is None:
            self._pub_place = self.get_via_config_value(
                "place", self.config.work
            )
        return self._pub_place

    @property
    def work_title(self):
        if self._work_title is None:
            self._work_title = self.get_via_config_value(
                "title", self.config.work
            )
        return self._work_title

    @property
    def work_id(self):
        if self._work_id is None:
            self._work_id = self.get_via_config_value(
                "id", self.config.work, multiple=True
            )
        return self._work_id

    @property
    def edition_title(self):
        if self._edition_title is None:
            self._edition_title = self.get_via_config_value(
                "title", self.config.attributes["edition"]
            )
        return self._edition_title

    @property
    def edition_license_url(self):
        if self._edition_license_url is None:
            self._edition_license_url = self.get_via_config_value(
                "url", self.config.edition["license"]
            )
        return self._edition_license_url

    @property
    def edition_license_title(self):
        if self._edition_license_title is None:
            self._edition_license_title = self.get_via_config_value(
                "title", self.config.edition["license"]
            )
        return self._edition_license_title

    @property
    def pub_date_edition(self):
        if self._pub_date_edition is None:
            self._pub_date_edition = self.get_via_config_value(
                "date", self.config.edition
            )
        return self._pub_date_edition

    @property
    def edition_pub_place(self):
        if self._edtion_pub_place is None:
            self._edtion_pub_place = self.get_via_config_value(
                "place", self.config.edition
            )
        return self._edtion_pub_place

    @property
    def edition_author_fullname(self):
        if self._edition_author_fullname is None:
            self._edition_author_fullname = self.get_via_config_value(
                "fullname", self.config.edition["author"]
            )
            if not self._edition_author_fullname:
                if (
                    self.edition_author_lastname
                    and self.edition_author_firstname
                ):
                    self._edition_author_fullname = ", ".join(
                        [
                            self.edition_author_lastname,
                            self.edition_author_firstname,
                        ]
                    )
        return self._edition_author_fullname

    @property
    def edition_author_firstname(self):
        if self._edition_author_firstname is None:
            self._edition_author_firstname = self.get_via_config_value(
                "firstname", self.config.edition["author"]
            )
        return self._edition_author_firstname

    @property
    def edition_author_lastname(self):
        if self._edition_author_lastname is None:
            self._edition_author_lastname = self.get_via_config_value(
                "lastname", self.config.edition["author"]
            )
        return self._edition_author_lastname

    @property
    def edition_author_id(self):
        if self._edition_author_id is None:
            self._edition_author_id = self.get_via_config_value(
                "id", self.config.edition["author"]
            )
        return self._edition_author_id

    @property
    def language(self):
        if self._language is None:
            self._language = self.get_via_config_value(
                "language", self.config.edition
            )
            if self._language:
                self._language = self._language.split("-")[0]
                try:
                    self._language = Lang(self._language).pt3
                except InvalidLanguageValue as e:
                    log.warning(e)
                    log.warning("Did not set language for %s" % self)

        return self._language

    @property
    def author_id(self):
        if self._author_id is None:
            self._author_id = self.get_via_config_value(
                "id", self.config.work["author"]
            )
        return self._author_id

    @property
    def author_fullname(self, *args):
        if self._author_fullname is None:
            self._author_fullname = self.get_via_config_value(
                "fullname", self.config.work["author"]
            )
            if not self._author_fullname:
                if self.author_lastname and self.author_firstname:
                    self._author_fullname = (
                        f"{self.author_lastname}, {self.author_firstname}"
                    )
        return self._author_fullname

    @property
    def author_firstname(self):
        if self._author_firstname is None:
            self._author_firstname = self.get_via_config_value(
                "firstname", self.config.work["author"]
            )
        return self._author_firstname

    @property
    def author_lastname(self):
        if self._author_lastname is None:
            self._author_lastname = self.get_via_config_value(
                "lastname", self.config.work["author"]
            )
        return self._author_lastname

    @property
    def genre(self):
        # NOTE: This opens up a wider field, than it seems
        # Especially, as there is no clear definition/vocabulary on how 'genre'
        # needs to be described
        if self._genre is None:
            self._genre = self.get_via_config_value("genre", self.config.work)
        return self._genre

    @property
    def wordcount(self):
        if self._wordcount is None:
            self._wordcount = self.get_via_config_value(
                "wordcount", self.config.edition
            )
        return self._wordcount

    # **********
    # ELTeC specs
    @property
    def eltec_time_slot(self):
        if self._eltec_time_slot is None:
            self._eltec_time_slot = self.get_via_config_value(
                "time_slot", self.config.eltec_specs
            )
        return self._eltec_time_slot

    @property
    def eltec_author_gender(self):
        if self._eltec_author_gender is None:
            # idea is to try to get parameter directly from xpath value
            self._eltec_author_gender = self.get_via_config_value(
                "author_gender", self.config.eltec_specs
            )
            # and only 'generate' it, if it has not been found
            if self._eltec_author_gender:
                self._eltec_author_gender = gender_to_authorgender(
                    self._eltec_author_gender
                )
        return self._eltec_author_gender

    @property
    def eltec_size(self):
        if self._eltec_size is None:
            # idea is to try to get parameter directly from xpath value
            self._eltec_size = self.get_via_config_value(
                "size", self.config.eltec_specs
            )
            # and only 'generate' it, if it has not been found
            if not self._eltec_size:
                self._eltec_size = wordcount_to_size(self.wordcount)
        return self._eltec_size

    @property
    def eltec_reprint_count(self):
        if self._eltec_reprint_count is None:
            # idea is to try to get parameter directly from xpath value
            self._eltec_reprint_count = self.get_via_config_value(
                "reprint_count", self.config.eltec_specs
            )
            # ToDo:
            #   find an alternative xpaths and build formatter
        return self._eltec_reprint_count

    @property
    def eltec_corpus_collection(self):
        if self._eltec_corpus_collection is None:
            self._eltec_corpus_collection = self.get_via_config_value(
                "corpus_collection", self.config.eltec_specs
            )
        return self._eltec_corpus_collection

    # **********

    # MULTI fields
    # all fields, that can have multiple entries
    @property
    def rights_holder(self):
        if self._rights_holder is None:
            self._rights_holder = [
                c for c in self.config.rights_holder if c.get("fullname")
            ]
        return self._rights_holder

    @property
    def collector(self):
        if self._collector is None:
            self._collector = [
                c for c in self.config.collector if c.get("fullname")
            ]
        return self._collector

    def _get_classifications(self, config_method):
        classifications = []
        for classification in config_method:

            # get all values for each classification
            feature_sets = []
            for key in classification.keys():
                results = self._get_via_config_value(
                    classification[key], multiple=True
                )
                feature_sets.append(
                    {
                        "key": key,
                        "results": results if results else [],
                        "fixed_value": classification[key]["value"],
                    }
                )

            # get the minimum length of all results to initialize the
            # result list
            # we only initialize as many empty dicts as the minimum amount of
            # results
            max_length = max(len(d["results"]) for d in feature_sets)
            # if there are no results, initialize the list with one empty dict
            result = [
                {"id": None, "value": None, "url": None}
                for _ in range(max_length or 1)
            ]

            # fill the result list with the concrete values
            for d in feature_sets:
                key = d["key"]
                if d["fixed_value"]:
                    # set the fixed value for all results
                    for r in result:
                        r[key] = d["fixed_value"]
                else:
                    for i, value in enumerate(d["results"]):
                        result[i][key] = value

                        # if the value of 'id' is an URL, extract the ID
                        if key == "id" and value.startswith("http"):
                            result[i][key] = value.split("/")[-1]

            classifications += result

        return classifications

    @property
    def basic_classifications(self):
        if self._basic_classifications is None:
            self._basic_classifications = self._get_classifications(
                self.config.basic_classifications
            )
        return self._basic_classifications

    @property
    def gnd_subjects(self):
        if self._gnd_subjects is None:
            self._gnd_subjects = self._get_classifications(
                self.config.gnd_subjects
            )
        return self._gnd_subjects

    # **********

    def validate_attributes(self, requirements, get_messages=False):
        """Validates all required attributes"""
        self._validation_errors = ValidationCollectionConfig(
            requirements
        ).validate_required_attributes(self)
        if get_messages:
            return self._validation_errors
        return len(self._validation_errors) == 0

    @property
    def images(self):
        """Returns a list of all images in the TEI file"""
        if self._images is None:
            self._images = []
            for xpath in self.config.images:
                image_paths = self.findall(xpath)
                for image_path in image_paths:
                    filename = os.path.basename(image_path)
                    filename_pure, filename_ext = os.path.splitext(filename)
                    image_path_stripped = image_path.lstrip(".").lstrip("/")
                    image = {
                        "xpath": xpath,
                        "path_original": image_path,
                        "path_full": os.path.join(
                            self.path, image_path_stripped
                        ),
                        "filename": filename,
                        "filename_pure": filename_pure,
                        # "filename_ext": filename_ext.lstrip("."),
                        "mimetype": guess_type(filename)[0],
                    }
                    if os.path.exists(image["path_full"]):
                        self._images.append(image)
                    else:
                        log.warning(
                            f"Image {image['path_full']} does not exist"
                        )
        return self._images

    def get_attributes(self, with_images=False):
        if self._attributes is None:
            self._attributes = {
                "id": self.pure_filename,
                "rights_holder": self.rights_holder,
                "collector": self.collector,
                "work": {
                    "id": self.work_id,
                    "title": self.work_title,
                    "author": {
                        "id": self.author_id,
                        "fullname": self.author_fullname,
                    },
                    "genre": self.genre,
                    "dateOfCreation": {
                        "date": self.work_date,
                        "range": self.work_dateRange,
                        "default": self.work_dateDefault,
                    },
                    "pub_place": self.pub_place,
                },
                "edition": {
                    "title": self.edition_title,
                    "pub_date": self.pub_date_edition,
                    "pub_place": self.edition_pub_place,
                    "author": {
                        "fullname": self.edition_author_fullname,
                        "id": self.edition_author_id,
                    },
                    "license": {
                        "url": self.edition_license_url,
                        "title": self.edition_license_title,
                    },
                    "language": self.language,
                },
                "eltec": {
                    "time_slot": self.eltec_time_slot,
                    "gender": self.eltec_author_gender,
                    "size": self.eltec_size,
                    "reprint_count": self.eltec_reprint_count,
                    "corpus_collection": self.eltec_corpus_collection,
                },
                "basic_classifications": self.basic_classifications,
                "gnd_subjects": self.gnd_subjects,
            }
            if with_images:
                self._attributes["images"] = self.images
            self._attributes = strip_strings_in_dict(self._attributes)
        return self._attributes

    def get_attribute(self, key):
        return self.get_attributes().get(key, None)
