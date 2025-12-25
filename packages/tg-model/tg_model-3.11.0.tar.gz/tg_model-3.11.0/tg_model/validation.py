# -*- coding: utf-8 -*-
# Copyright (C) 2025 TUD | ZIH
# ralf.klammer@tu-dresden.de

import logging

import re

from datetime import datetime

log = logging.getLogger(__name__)

HUMAN_READABLE_MESSAGES = {
    "collection.attributes.work.dateOfCreation.date": (
        "Work/Date of Creation: Date is undefined!"
    ),
    "collection.attributes.work.dateOfCreation.notAfter": (
        "Work/Date of Creation: 'notAfter' needs a defintion, \
        cause 'notBefore' is defined!"
    ),
    "collection.attributes.work.dateOfCreation.notBefore": (
        "Work/Date of Creation: 'notBefore' needs a defintion, \
        cause 'notAfter' is defined!"
    ),
    "collection.attributes.edition.license.title": (
        "Edition/License: Title is undefined!"
    ),
    "collection.attributes.edition.license.url": (
        "Edition/License: URL is undefined!"
    ),
    "collection.attributes.work.genre": "Work/General: Genre is undefined!",
    "collection.rights_holder": (
        "Basic Attributes/Rights Holder: Min. 1 rights holder needs to be \
        defined!"
    ),
    "collection.collector": (
        "Basic Attributes/Collector: Min. 1 collector needs to be defined!"
    ),
}


class ValidationCollectionConfig:
    def __init__(self, requirements):
        self.requirements = requirements

    def _validate_iso_date(self, date_str):
        """Validates a date in ISO format (YYYY-MM-DD)"""
        if not date_str:
            return False
        try:
            # Handles negative years & converts to string
            date_str = str(date_str).lstrip("-")
            # Completes incomplete dates
            if len(date_str) == 4:  # Only year
                date_str += "-01-01"
            elif len(date_str) == 7:  # Year and month
                date_str += "-01"
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def validate_required_attributes(self, tei_parser):
        """Validates all required attributes defined in REQUIRED_ATTRIBUTES"""
        errors = []

        def check_nested_attributes(rules, _obj_name, parser):
            for key, value in rules.items():
                obj_name = f"{_obj_name}.{key}" if _obj_name else key
                if value.get("required"):
                    value = value.get("required")
                    attr_value = getattr(parser, value.get("attr_name"), None)
                    if not attr_value:
                        errors.append(
                            {
                                "obj_name": obj_name,
                                "attr_value": attr_value,
                                "type": "undefined",
                                "and_attrib": value.get("and_attrib"),
                                "or_attrib": value.get("or_attrib"),
                            }
                        )
                    elif value.get("iso_date") and not self._validate_iso_date(
                        attr_value
                    ):
                        errors.append(
                            {
                                "obj_name": obj_name,
                                "attr_value": attr_value,
                                "type": "iso_date",
                                "and_attrib": value.get("and_attrib"),
                                "or_attrib": value.get("or_attrib"),
                            }
                        )
                else:
                    check_nested_attributes(value, obj_name, parser)

        check_nested_attributes(self.requirements, "", tei_parser)
        i = 0

        to_be_removed = []
        for error in errors:
            if error["type"] == "undefined" and error["or_attrib"]:
                for or_attr in error["or_attrib"]:
                    if (
                        getattr(tei_parser, or_attr, None)
                        and error not in to_be_removed
                    ):
                        to_be_removed.append(error)
            if error["type"] == "undefined" and error["and_attrib"]:
                for and_attr in error["and_attrib"]:
                    if not getattr(tei_parser, and_attr, None):
                        if error not in to_be_removed:
                            to_be_removed.append(error)
            i += 1
        for i in to_be_removed:
            errors.remove(i)

        error_messages = []
        for error in errors:
            if error["type"] == "undefined":
                if error["obj_name"] in HUMAN_READABLE_MESSAGES:
                    message = HUMAN_READABLE_MESSAGES[error["obj_name"]]
                else:
                    message = f"Attribute {error['obj_name']} with value\
                        {error['attr_value']} is required."
                error_messages.append(message)

        if errors:
            log.warning("*" * 10)
            log.warning(
                f"Found {len(errors)} validation errors in document:\
                    {tei_parser.filename}"
            )
        for error in errors:
            if error["type"] == "undefined":
                log.warning(
                    f"Invalid attribute {error['obj_name']}: {error['attr_value']} will cause PROBLEMS in final Publication!"
                )
            elif error["type"] == "iso_date":
                log.warning(
                    f"Invalid ISO date format for {error['obj_name']}: {error['attr_value']} will cause PROBLEMS in final Publication!"
                )
        if errors:
            log.warning("*" * 10)
        return error_messages
