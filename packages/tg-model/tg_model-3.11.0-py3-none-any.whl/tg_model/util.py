# -*- coding: utf-8 -*-
# Copyright (C) 2023-2025 TUD | ZIH
# ralf.klammer@tu-dresden.de

import logging

import re

from functools import reduce
from jinja2 import FileSystemLoader, PackageLoader, Environment  # type: ignore
from lxml.etree import QName  # type: ignore
from os import getcwd, listdir, mkdir
from os.path import exists, isfile, join, commonprefix, isdir
from pathlib import PurePath, Path


log = logging.getLogger(__name__)


def cli_startup(log_level=logging.INFO, log_file=None):
    log_config = dict(
        level=log_level,
        format="%(asctime)s %(name)-10s %(levelname)-4s %(message)s",
    )
    if log_file:
        log_config["filename"] = log_file

    logging.basicConfig(**log_config)
    logging.getLogger("").setLevel(log_level)


def get_files(path, as_tuple=False, file_ext="xml"):
    """
    Get all files with a specific extension in a directory and its subdirectories.
    Args:
        path (str): The directory path to search in.
        as_tuple (bool): If True, return a tuple with the directory and file name.
                         If False, return the full file path as a string.
        file_ext (str): The file extension to look for (default is "xml").
    Returns:
        list: A list of file paths or tuples containing the directory and file name.
    """
    log.debug(f"Searching for files with extension .{file_ext} in {path}")
    result = []
    for entry in listdir(path):
        full_path = join(path, entry)
        log.debug(f"Checking {full_path} for files with extension .{file_ext}")
        log.debug(f"Is file: {isfile(full_path)}")
        log.debug(f"Is directory: {isdir(full_path)}")
        if isfile(full_path) and Path(entry).suffix == f".{file_ext}":
            # If as_tuple is True, return a tuple with path and entry
            # Otherwise, return the full path as a string
            result.append((path, entry) if as_tuple else full_path)
        elif isdir(full_path):
            # Count matching files in subdirectory
            matching_files = [
                (full_path, subdir) if as_tuple else join(full_path, subdir)
                for subdir in listdir(full_path)
                if isfile(join(full_path, subdir))
                and Path(subdir).suffix == f".{file_ext}"
            ]
            # If there is exactly one matching file, add it to the result
            if len(matching_files) == 1:
                result.append(matching_files[0])
            else:
                log.warning(
                    "%s files with extension .%s found in %s"
                    % (
                        "No" if not len(matching_files) else "Multiple",
                        file_ext,
                        full_path,
                    )
                )
    return result


def get_image_files(path, as_tuple=False, image_exts=None):
    """
    Get all image files in a directory and its subdirectories.
    Args:
        path (str): The directory path to search in.
        as_tuple (bool): If True, return a tuple with the directory and file name.
                         If False, return the full file path as a string.
        image_exts (list or None): List of image file extensions (default: common formats).
    Returns:
        list: A list of file paths or tuples containing the directory and file name.
    """
    if image_exts is None:
        image_exts = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".webp",
        ]
    log.debug(
        f"Searching for image files in {path} with extensions: {image_exts}"
    )
    result = []
    for entry in listdir(path):
        full_path = join(path, entry)
        log.debug(f"Checking {full_path} for image files")
        log.debug(f"Is file: {isfile(full_path)}")
        log.debug(f"Is directory: {isdir(full_path)}")
        if isfile(full_path) and Path(entry).suffix.lower() in image_exts:
            result.append((path, entry) if as_tuple else full_path)
        elif isdir(full_path):
            matching_files = [
                (full_path, subdir) if as_tuple else join(full_path, subdir)
                for subdir in listdir(full_path)
                if isfile(join(full_path, subdir))
                and Path(subdir).suffix.lower() in image_exts
            ]
            if len(matching_files) == 1:
                result.append(matching_files[0])
            elif len(matching_files) > 1:
                log.warning(
                    f"Multiple image files found in {full_path}: {matching_files}"
                )
    return result


def add_directory(path):
    if not exists(path):
        mkdir(path)


def get_tag(elem):
    if elem is not None:
        tag = QName(elem)
        return tag.localname


def get_type(*args, **kw):
    log.debug('Deprecated function "get_type')
    return get_tag(*args, **kw)


def get_unique_node_id(node):
    # build a kind of id
    return "_".join(
        [node.tag] + ["_".join(list(item)) for item in node.items()]
    )


def build_xpath(elem, xpath="", include_items=False):
    xpath += "/" + get_type(elem)
    # if include_items:
    #     for item in elem.items():
    #         xpath += '[@%s="%s"]' % item
    return xpath


def prepare_path(path, create=False, subpath=None):
    log.debug(f"prepare_path: {path} subpath: {subpath}")

    path = Path(path)

    if subpath:
        path = path / subpath

    if path.is_absolute():
        path = path.resolve()
    else:
        path = Path.cwd() / path

    if create and not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    return str(path)


def check_outpath(out):
    log.debug("Deprecated: `check_outpath`")
    parts = prepare_path(out).split("/")
    for i in range(len(parts)):
        if not parts[i]:
            continue
        subpath = "/".join(parts[0 : i + 1])
        log.debug("exists %s: %s" % (subpath, exists(subpath)))
        if not exists(subpath):
            log.debug("mkdir %s" % subpath)
            mkdir(subpath)
    return out


def split_xpath(xpath):
    result = {
        "xpath": xpath,
        "full_path": xpath,
        # rvalue ~= return value
        "rvalue": "text",
        # akey ~= additional key
        "akey": None,
    }
    if xpath.find("^") != -1 and xpath.find("~") == -1:
        result["xpath"], result["rvalue"] = xpath.split("^")
    elif xpath.find("^") == -1 and xpath.find("~") != -1:
        result["xpath"], result["akey"] = xpath.split("~")
    elif xpath.find("^") == -1 and xpath.find("~") != -1:
        # ToDO
        log.error("Currently not able to handle both steering commands!")
    return result


# source of that nice function: https://stackoverflow.com/a/47969823/3756733
def deref_multi(data, keys):
    return reduce(lambda d, key: d[key], keys, data)


def find_tei_directory(path, tei_directory, depth):
    log.debug("***find_tei_directory***")
    log.debug((path, tei_directory, depth))
    subpaths = []
    # create list containing only subpaths of "current" path
    dirlist = [d for d in listdir(path) if isdir("%s/%s" % (path, d))]
    for subpath in dirlist:
        fullpath = "%s/%s" % (path, subpath)
        # append path if:
        #   - found a path having the same name as he given 'tei_directory' AND
        #   - it has xml-files inside
        if subpath == tei_directory and len(
            get_files(fullpath, file_ext="xml")
        ):
            subpaths.append(fullpath)
            break
        else:
            subpaths += find_tei_directory(fullpath, tei_directory, depth + 1)
    return subpaths


def is_valid_date(date_string):
    date_string = str(date_string)
    test = any(
        [
            # 4 digits, e.g.: 1876
            re.match(r"^\d{4}$", date_string),
            # 4 digits followed by 2 sets of 2 digits,
            # seperated by a non-digit char, e.g.: 1876-12-24
            re.match(r"^\d{4}\D\d{2}\D\d{2}$", date_string),
            # 2 sets of 2 digits followed by 4 digits,
            # seperated by a non-digit char, e.g.: 24.12.1876
            # re.match(r"^\d{2}\D\d{2}\D\d{4}$", date_string),
            # 4 digits followed by a space and 2 digits, e.g.: 2016 12
            re.match(r"^\d{4}\D\d{2}$", date_string),
            # 8 digits in the format YYYYMMDD, e.g.: 20040711
            re.match(r"^\d{8}$", date_string),
        ]
    )
    if not test:
        log.warning("is_valid_date - Invalid date: %s" % date_string)
    return test


def find_name_of_subproject(projectname, subproject_path, tei_directory):
    # check if projectname is in path of subproject (case insensitive)
    pn_in_spp = re.search(projectname, subproject_path, re.IGNORECASE)
    if pn_in_spp:
        # trim path of subproject after projectname
        sp_trimmed = subproject_path[pn_in_spp.end() :]
        if sp_trimmed.startswith("/"):
            # remove "/" if necessary
            sp_trimmed = sp_trimmed[1:]
        # check if tei_directory is in trimmed path of subproject
        teid_in_spp = re.search(tei_directory, sp_trimmed, re.IGNORECASE)
        if teid_in_spp:
            # remove tei_directory incl. leading "/" (-> -1)
            sp_trimmed = sp_trimmed[: teid_in_spp.start() - 1]
        return sp_trimmed.replace("/", "_")


def extract_unique_name(paths):
    """
    Extracts the unique parts from a list of paths.
    Dynamically finds the common prefix and suffix and removes them.
    """

    # Find common prefix
    common_prefix = commonprefix(paths)

    # Find common suffix by reversing the strings
    reversed_paths = [path[::-1] for path in paths]
    common_suffix = commonprefix(reversed_paths)[::-1]

    # Remove prefix and suffix
    result = []
    for path in paths:
        unique = path[len(common_prefix) :]
        if common_suffix:
            unique = unique[: -len(common_suffix)]
        # Remove leading/trailing slashes
        unique = unique.strip("/")
        result.append(unique)

    return result


def strip_strings_in_dict(_dict):
    for key in _dict:
        if isinstance(_dict[key], dict):
            strip_strings_in_dict(_dict[key])
        elif isinstance(_dict[key], list):
            for item in _dict[key]:
                if isinstance(item, dict):
                    strip_strings_in_dict(item)
                elif isinstance(item, str):
                    item = item.strip()
                else:
                    log.warning(
                        "strip_strings_in_dict - Unknown type: %s"
                        % item.__class__
                    )
        elif isinstance(_dict[key], str):
            _dict[key] = _dict[key].strip()
    return _dict


def all_not_none(_array):
    return all([item is not None for item in _array])


class RenderBase(object):
    def __init__(self, projectpath, templates=None):
        """
        Initialize the RenderBase class.

        Args:
            projectpath: Path to the project.
            templates: Path to the templates directory (optional).
        """
        self.projectpath = projectpath

        if templates:
            templateLoader = FileSystemLoader(searchpath=templates)
        else:
            templateLoader = PackageLoader("tg_model", "templates")
        self.templateEnv = Environment(
            loader=templateLoader, trim_blocks=True, lstrip_blocks=True
        )
        # Add some Python functions to Jinja environment
        self.templateEnv.globals.update(
            all=all, any=any, all_not_none=all_not_none
        )

    def render(self, output, content, templatefile, skip_if_exists=False):
        """
        Renders a template into an output file.

        Args:
            output: Output path.
            content: Template context.
            templatefile: Name of the template.
            skip_if_exists: Skip if file exists (default: False).
        """
        if skip_if_exists and exists(output):
            log.debug(f"Skipping existing file: {output}")
            return False

        template = self.templateEnv.get_template(templatefile)
        log.debug(output)
        with open(output, "w", encoding="utf-8") as f:
            f.write(template.render(content))
        return True
