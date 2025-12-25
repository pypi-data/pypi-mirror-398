# -*- coding: utf-8 -*-
# Copyright (C) 2025 TUD | ZIH
# ralf.klammer@tu-dresden.de

import logging

import csv

log = logging.getLogger(__name__)


class CSVExport:

    def __init__(self, seperator=".", *args, **kw):
        # Initialize the CSVExport class with a separator and other arguments
        self.flat_dicts = []
        self.seperator = seperator

    def _flatten_dict(self, d, parent_key="", init_list=False):
        # Recursively flatten a dictionary
        for k, v in d.items():
            new_key = f"{parent_key}{self.seperator}{k}" if parent_key else k
            if init_list:
                self._flat_dict[new_key] = []
            if isinstance(v, dict):
                # If the value is a dictionary, recursively flatten it
                self._flatten_dict(v, new_key)
            elif isinstance(v, list):
                # If the value is a list, iterate through its items
                for item in v:
                    if isinstance(item, dict):
                        # If the item is a dictionary, recursively flatten it
                        self._flatten_dict(item, new_key, init_list=True)
            else:
                # If the key already exists, convert it to a list and append
                # the new value
                if new_key in self._flat_dict:
                    if not isinstance(self._flat_dict[new_key], list):
                        self._flat_dict[new_key] = [self._flat_dict[new_key]]
                    else:
                        log.debug("Key already exists: %s" % new_key)
                    if v:
                        # Append the value to the list if it is not empty
                        self._flat_dict[new_key].append(v)
                else:
                    # Otherwise, just set the value
                    self._flat_dict[new_key] = v
        return self._flat_dict

    def add_dict(self, dictionary):
        # Reset the flat dictionary
        self._flat_dict = {}
        # Flatten the dictionary and add it to the list of flat dictionaries
        self.flat_dicts.append(self._flatten_dict(dictionary))

    def write_csv(
        self,
        name=None,
        basepath=None,
        delimiter="\t",
        encoding="utf-8",
        suffix=".tsv",
        **kwargs,
    ):
        """
        Writes the collected flat dictionaries to a CSV file.

        Args:
            name (str): Name of the output file (without suffix)
            basepath (str, optional): Base directory path
            delimiter (str, optional): CSV delimiter. Default is "\t"
            encoding (str, optional): File encoding. Default is "utf-8"
            suffix (str, optional): File suffix. Default is ".tsv"
        """

        if not self.flat_dicts:
            log.warning("No data available for export")
            return

        outfile = f"{basepath}/{name}{suffix}"
        log.info(f"Exporting CSV to {outfile}")

        # Collect all existing columns (keys)
        fieldnames = set()
        for d in self.flat_dicts:
            fieldnames.update(d.keys())
        fieldnames = sorted(list(fieldnames))

        # Write CSV
        with open(outfile, "w", newline="", encoding=encoding) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                delimiter=delimiter,
                quoting=csv.QUOTE_MINIMAL,
            )

            # Write header
            writer.writeheader()

            # Write data
            for flat_dict in self.flat_dicts:
                # Convert lists to strings
                row = {}
                for key, value in flat_dict.items():
                    if isinstance(value, list):
                        row[key] = "; ".join(str(x) for x in value)
                    else:
                        row[key] = value
                writer.writerow(row)
        return outfile
