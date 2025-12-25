# -*- coding: utf-8 -*-
# Copyright (C) 2023-2025 TUD | ZIH
# ralf.klammer@tu-dresden.de

import logging

from copy import deepcopy

from yaml import full_load as load_yaml  # type: ignore
from pkgutil import get_data
from os import listdir, path
from pyaml import dump as dump_yaml  # type: ignore


from .other_files import OtherFiles
from .util import (
    split_xpath,
    exists,
    find_name_of_subproject,
    prepare_path,
    get_files,
    deref_multi,
    find_tei_directory,
    strip_strings_in_dict,
    extract_unique_name,
)

log = logging.getLogger(__name__)

IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".tiff",
    ".bmp",
    ".svg",
    ".ico",
)


class CollectionMixin(object):
    @property
    def multi_attribs(self):
        return [
            "basic_classifications",
            "rights_holder",
            "collector",
            "gnd_subjects",
            "images",
        ]

    @property
    def xpath_or_value_attribs(self):
        return [
            "author_id",
            "author_fullname",
            "author_firstname",
            "author_lastname",
            "genre",
            "language",
            "wordcount",
            "work_title",
            "work_publication_date",
            "work_publication_place",
            "edition_title",
            "edition_author",
            "edition_author_id",
            "edition_publication_date",
            "edition_publication_place",
            "eltec_author_gender",
            "eltec_reprintCount",
            "eltec_size",
            "eltec_time_slot",
            "work_id",
            "work_publication_notBefore",
            "work_publication_notAfter",
            "edition_license_title",
            "edition_license_url",
            "eltec_corpus",
            "eltec_size",
        ]

    @staticmethod
    def _create_property(key, parent_prop, is_list=False):
        """Generator for properties with optional list support.

        Args:
            key (str): Key for dictionary access.
            parent_prop (str): Name of the parent property.
            is_list (bool): True if the property should return a list.
        """

        def getter(self):
            parent = getattr(self, parent_prop, None)
            if parent is None:
                return [] if is_list else None

            # Initialize key if it doesn't exist
            if key not in parent:
                parent[key] = [] if is_list else {}

            # Get the value associated with the key from the parent dictionary
            value = parent.get(key)
            if is_list:
                # Handle properties, that should return a list
                if isinstance(value, dict) and "xpaths" in value:
                    # Return xpath list if available
                    # Note: This is currently only used for images
                    return value.get("xpaths")
                elif not isinstance(value, list):
                    # Return empty list if value is not a list
                    return []
            # Return the value directly for non-list properties
            return value

        def setter(self, content):
            # Retrieve the parent property
            parent = getattr(self, parent_prop, None)
            if parent is None:
                # Initialize the parent property if it does not exist
                setattr(self, parent_prop, {})
                parent = getattr(self, parent_prop)
            # Set the content for the specified key
            parent[key] = content

        return property(getter, setter)

    # COLLECTION
    collection = _create_property("collection", "content")

    title = _create_property("title", "collection")
    short_title = _create_property("short", "title")
    long_title = _create_property("long", "title")

    # WORK
    work = _create_property("work", "attributes")

    genre = _create_property("genre", "work")
    work_title = _create_property("title", "work")
    work_id = _create_property("id", "work")

    author = _create_property("author", "work")
    author_fullname = _create_property("fullname", "author")
    author_firstname = _create_property("firstname", "author")
    author_lastname = _create_property("lastname", "author")
    author_id = _create_property("id", "author")
    work_publication_place = _create_property("place", "work")

    dateOfCreation = _create_property("dateOfCreation", "work")
    work_publication_date = _create_property("date", "dateOfCreation")
    work_publication_notBefore = _create_property(
        "notBefore", "dateOfCreation"
    )
    work_publication_notAfter = _create_property("notAfter", "dateOfCreation")

    # EDITION
    edition = _create_property("edition", "attributes")
    language = _create_property("language", "edition")
    wordcount = _create_property("wordcount", "edition")
    edition_title = _create_property("title", "edition")
    edition_license = _create_property("license", "edition")
    edition_license_title = _create_property("title", "edition_license")
    edition_license_url = _create_property("url", "edition_license")
    edition_author = _create_property("author", "edition")
    edition_publication_date = _create_property("date", "edition")
    edition_publication_place = _create_property("place", "edition")

    # ELTEC SPECS
    eltec_specs = _create_property("eltec_specs", "collection")
    eltec_author_gender = _create_property("author_gender", "eltec_specs")
    eltec_reprintCount = _create_property("reprintCount", "eltec_specs")
    eltec_size = _create_property("size", "eltec_specs")
    eltec_time_slot = _create_property("time_slot", "eltec_specs")
    eltec_corpus = _create_property("corpus_collection", "eltec_specs")
    eltec_size = _create_property("size", "eltec_specs")

    # ELEMENTS
    elements = _create_property("elements", "collection")

    # MULTI ATTRIBUTES
    rights_holder = _create_property(
        "rights_holder", "collection", is_list=True
    )
    collector = _create_property("collector", "collection", is_list=True)
    basic_classifications = _create_property(
        "basic_classifications", "collection", is_list=True
    )
    gnd_subjects = _create_property("gnd_subjects", "collection", is_list=True)

    images = _create_property("images", "collection", is_list=True)

    @property
    def sorted_elements(self):
        return sorted(self.elements, key=lambda x: (x["filename"]))


class YAMLConfigBase(object):
    def __init__(
        self, filename, projectpath=None, subproject=None, *args, **kw
    ):
        self.filename = filename
        self.projectpath = projectpath
        self.subproject = subproject
        self._content = False
        self._path = None

    @property
    def path(self):
        if self._path is None:
            if self.subproject:
                self._path = "%s/%s" % (
                    self.subproject["basepath"],
                    getattr(self, "outname", self.filename),
                )
            else:
                self._path = "%s/%s" % (self.projectpath, self.filename)
        return self._path

    @property
    def content(self):
        if self._content is False:
            self._content = None
            _data = self.get_data()
            if _data:
                self._content = load_yaml(_data)
        return self._content

    def get_data(self):
        if exists(self.path):
            with open(self.path, "rb") as file:
                return file.read()
        else:
            log.error("%s does not exist!" % self.path)

    def _get(self, key, _dict=None):
        _dict = self.content if _dict is None else _dict
        if key not in _dict:
            return None
        else:
            value = _dict[key]
            log.debug("[_get] value: %s | key: %s" % (value, key))
            return value if value else {}

    def get(self, key, section=None, default=None):
        section_name = section
        section = None
        if section_name:
            section = self._get(section_name)
            if section is None:
                log.error(
                    "Section_name: '%s' not found in %s"
                    % (section_name, self.path)
                )
        value = self._get(key, _dict=section)
        if value:
            return value
        else:
            log.info(
                "'%s' not found in section_name: %s (%s)"
                % (key, section_name, self.path)
            )
            return default

    def exists(self):
        log.debug("This check for existance is very rough!!!")
        return bool(self.content)


class ProjectConfig(YAMLConfigBase):

    _config_file = "project.yaml"
    _legacy_config_file = "main.yaml"

    def __init__(self, *args, **kw):
        super().__init__(self._config_file, *args, **kw)
        self._check_config()

        self.other_files = OtherFiles(self.projectpath, self)

    @property
    def project(self):
        return self.content.get("project")

    @property
    def title(self):
        return self.project.get("title", None)

    @title.setter
    def title(self, title):
        self.project["title"] = title

    @property
    def description(self):
        return self.project.get("description", None)

    @description.setter
    def description(self, description):
        self.project["description"] = description

    @property
    def avatar(self):
        return self.project.get("avatar", None)

    @avatar.setter
    def avatar(self, avatar):
        self.project["avatar"] = avatar

    @property
    def xslt(self):
        return self.project.get("xslt", None)

    @xslt.setter
    def xslt(self, xslt):
        self.project["xslt"] = xslt

    @property
    def collectors(self):
        return [c for c in self.project.get("collectors", []) if c.get("name")]

    @collectors.setter
    def collectors(self, collectors):
        self.project["collectors"] = collectors

    def _check_config(self):
        """
        Check for config files in the following order:
        1. project.yaml (preferred)
        2. main.yaml (legacy)

        Returns:
            str: Name of the found config file or None if no config file exists

        Note:
            This method ensures backward compatibility, see #38
        """
        project_path = path.join(self.projectpath, self._config_file)
        legacy_path = path.join(self.projectpath, self._legacy_config_file)

        if path.exists(project_path):
            self.filename = self._config_file
        elif path.exists(legacy_path):
            log.warning(
                f"Using legacy config file '{self._config_file}'!"
                f"Please rename to '{self._legacy_config_file}'"
                f"as '{self._config_file}' is already deprecated!"
            )
            self.filename = self._legacy_config_file

        # else:
        #     raise FileNotFoundError(
        #         "No config file found in %s" % self.projectpath
        #     )

    def validate(self):
        request = []
        # check if there are any files in the given inputpath
        for subproject in self.content["subprojects"]:
            if not get_files(subproject["inpath"]):
                request.append(
                    "No XML files found at: %s" % subproject["inpath"]
                )
        return request

    def _check_files(self):
        save = False
        for subproject in self.content["subprojects"]:
            if "files" not in subproject:
                subproject["files"] = sorted(get_files(subproject["inpath"]))
                save = True
        if save:
            self.save()

    def get_subprojects(self):
        if self.exists():
            self._check_files()
            return deepcopy(self.content["subprojects"])
        else:
            return []

    def get_subproject(self, name=None, inpath=None):
        for sp in self.get_subprojects():
            if name and sp["name"] == name:
                return sp
            if inpath and sp["inpath"] == inpath:
                return sp
        return None

    @property
    def min_hitrate(self):
        return self.get("min_hitrate", section="proposals", default=50)

    def set_subproject_stats(self):
        for subproject in self.get_subprojects():
            files = [
                f
                for f in listdir(subproject["inpath"])
                if not path.isdir("%s/%s" % (subproject["inpath"], f))
            ]
            subproject["stats"] = {"files": len(files)}

    def save(self):
        with open(self.path, "w") as file:
            file.write(dump_yaml(self.content))

    def update(
        self,
        inputpath=None,
        sourcepath=None,
        tei_directory=None,
        tei_directories=None,
        **kw,
    ):
        if sourcepath and tei_directory:
            tei_directories = find_tei_directory(sourcepath, tei_directory, 0)
        elif inputpath:
            tei_directories = inputpath.split(",")
        elif tei_directories is not None:
            pass
        else:
            log.error("Neither 'sourcepath' nor 'inputpath' is defined!")
            raise ValueError

        log.debug("tei_directories: %s" % tei_directories)
        existing_subprojects = []
        for sp in self.get_subprojects():
            if sp["inpath"] in tei_directories:
                existing_subprojects.append(sp["name"])
            else:
                # shutil.rmtree(sp["basepath"])
                self.content["subprojects"].remove(sp)

        # ToDo: merge the following code with the same code in
        # ProjectConfigTemplate.render
        for p in tei_directories:
            prepared_path = prepare_path(p)
            splitted_pp = prepared_path.split("/")
            length = 3 if len(splitted_pp) >= 3 else len(splitted_pp)

            if sourcepath:
                # try to find name of subproject only if there is more
                # than one subproject
                if len(tei_directories) > 1:
                    input_name = find_name_of_subproject(
                        kw["projectname"], p, tei_directory
                    )
                if len(tei_directories) <= 1 or not input_name:
                    input_name = sourcepath.split("/")[-1]
            else:
                input_name = "_".join(splitted_pp[-length:])

            if input_name in existing_subprojects:
                continue

            outpath = prepare_path(
                (
                    kw["outputpath"]
                    if "outputpath" in kw and kw["outputpath"]
                    else self.projectpath
                ),
                subpath="/".join([input_name, "result"]),
                create=True,
            )

            basepath = prepare_path(
                self.projectpath,
                subpath=input_name,
                create=True,
            )

            self.content["subprojects"].append(
                {
                    "inpath": prepared_path,
                    "name": input_name,
                    "outpath": outpath,
                    "basepath": basepath,
                    "files": sorted(get_files(prepared_path)),
                }
            )

        self.other_files.init(self.content["project"])
        self.save()

    def get_tg_session_id(self, instance):
        if (
            not self.content
            or not self.content.get("tg_session_id")
            or not self.content["tg_session_id"][instance]
        ):
            return None
        return self.content["tg_session_id"].get(instance)

    def set_tg_session_id(self, tg_session_id, instance="test"):
        if not self.content.get("tg_session_id"):
            self.content["tg_session_id"] = {"test": None, "live": None}
        self.content["tg_session_id"][instance] = tg_session_id
        self.save()

    def get_tg_project_id(self, instance):
        if (
            not self.content.get("tg_project_id")
            or not self.content["tg_project_id"][instance]
        ):
            return None
        return self.content["tg_project_id"].get(instance)

    def set_tg_project_id(self, tg_project_id, instance="test"):
        if not self.content.get("tg_project_id"):
            self.content["tg_project_id"] = {"test": None, "live": None}
        self.content["tg_project_id"][instance] = tg_project_id
        self.save()


class CollectionConfig(YAMLConfigBase, CollectionMixin):
    def __init__(self, *args, **kw):
        super().__init__("collection.yaml", *args, **kw)
        self._attributes = None
        self._work = None
        self._edition = None
        self._eltec_specs = None
        self._as_dict = None

    def save(self):
        cc_template = CollectionConfigTemplate(projectpath=self.projectpath)
        yaml_content = cc_template.dump_yaml_with_comments(
            self.content,
            cc_template.extracted_comments,
        )
        if not self.filename:
            raise Exception("No filename given for YAMLConfigTemplate!")
        with open(self.path, "w") as file:
            file.write(yaml_content)

    @property
    def attributes(self):
        if self._attributes is None:
            self._attributes = self.content["collection"]["attributes"]
        return self._attributes

    @property
    def work(self):
        if self._work is None:
            self._work = self.attributes["work"]
        return self._work

    @property
    def edition(self):
        if self._edition is None:
            self._edition = self.attributes["edition"]
        return self._edition

    @property
    def eltec_specs(self):
        if self._eltec_specs is None:
            self._eltec_specs = self.content["collection"]["eltec_specs"]
        return self._eltec_specs

    def get_missing_params(self):
        missing_params = []
        for k in ["short", "long"]:
            keys = ["collection", "title", k]
            if deref_multi(self.content, keys) is None:
                missing_params.append(".".join(keys))
        return missing_params

    def get_dict(self):
        if self._as_dict is None:
            self._as_dict = strip_strings_in_dict(self.content["collection"])
        return self._as_dict


class YAMLConfigTemplate(YAMLConfigBase):
    def __init__(self, filename, projectpath, subpath=None, *args, **kw):
        self.projectpath = prepare_path(projectpath, create=True)

        super().__init__(filename, self.projectpath, *args, **kw)
        self.extracted_comments = self.extract_attributes(
            attribute="comments", pop=True
        )
        self.extracted_requirements = self.extract_attributes(
            attribute="required", pop=True
        )

    def get_data(self):
        return get_data(__name__, "templates/%s" % self.filename)

    def dump_yaml_with_comments(self, data, comments_dict):
        """
        Dumps YAML with comments underneath each entry
        """
        yaml_lines = []

        def get_comments(path_parts):
            # Navigate through the nested structure
            current = comments_dict
            for part in path_parts:
                # If the current level is not a dictionary or the part is not
                # found, return an empty list
                if not isinstance(current, dict) or part not in current:
                    return []
                current = current[part]

            # If we reach the target, return the comments
            comments_list = current.get("comments")
            return comments_list if isinstance(comments_list, list) else []

        def set_comments(comments, yaml_lines, indent):
            if len(comments) > 1:
                for c in comments:
                    yaml_lines.append(f"{indent}# {c}")
            elif comments:
                return f"  # {comments[0]}"
            return ""

        def _dump_value_recursive(
            value, level=0, path_parts=[], list_indent=False
        ):
            """
            Recursively processes the given value (dictionary or list) and
            generates YAML lines with optional comments.

            Args:
            value: The data structure to process (dict, list, or scalar).
            level: The current indentation level.
            path_parts: The path to the current value in the data structure.
            list_indent: Custom indentation for list items, if applicable.
            """
            indent = "  " * level

            if isinstance(value, dict):
                i = 0
                for key, val in value.items():
                    # Skip entries with the key "comments"
                    if key == "comments":
                        continue

                    # Build the current path for nested structures
                    current_path = path_parts + [key]

                    # Retrieve and set comments for the current key
                    comment = set_comments(
                        get_comments(current_path),
                        yaml_lines,
                        indent,
                    )

                    # If the value is a dictionary or list, process
                    # it recursively
                    if isinstance(val, (dict, list)):
                        yaml_lines.append(f"{indent}{key}:{comment}")
                        _dump_value_recursive(val, level + 1, current_path)
                    else:
                        # Adjust indentation for list items if applicable
                        _indent = indent
                        if list_indent is not False and i == 0:
                            _indent = list_indent + "- "

                        # Handle None values and scalar values
                        if val is None:
                            yaml_lines.append(f"{_indent}{key}:{comment}")
                        else:
                            yaml_lines.append(
                                f"{_indent}{key}: {val}{comment}"
                            )
                    i += 1

            elif isinstance(value, list):
                # Handle empty lists
                if not value:
                    yaml_lines.append(f"{indent}[]")
                else:
                    for item in value:
                        if isinstance(item, dict):
                            # Get the first key-value pair of the dictionary
                            first_key = next(iter(item))
                            first_val = item[first_key]

                            # Add a list marker with the first key-value pair
                            if isinstance(first_val, (dict, list)):
                                yaml_lines.append(f"{indent}- {first_key}:")
                                # Recursively process the value if it's a dict or list
                                _dump_value_recursive(
                                    first_val, level + 2, path_parts
                                )
                            else:
                                yaml_lines.append(
                                    f"{indent}- {first_key}: {first_val or ''}"
                                )

                            # Process the rest of the dictionary
                            # (excluding the first key)
                            rest_dict = {
                                k: v for k, v in item.items() if k != first_key
                            }
                            if rest_dict:
                                _dump_value_recursive(
                                    rest_dict, level + 1, path_parts
                                )

                        elif isinstance(item, list):
                            # Recursively process nested lists
                            _dump_value_recursive(item, level, path_parts)
                        else:
                            # Add scalar values directly to the YAML output
                            yaml_lines.append(f"{indent}- {item}")

        _dump_value_recursive(data)
        return "\n".join(yaml_lines)

    def save(self):
        """
        Saves the YAML content to the file, including comments extracted
        earlier.
        """
        if not self.filename:
            raise Exception("No filename given for YAMLConfigTemplate!")
        yaml_content = self.dump_yaml_with_comments(
            self.content,
            self.extracted_comments,
        )

        with open(self.path, "w") as file:
            file.write(yaml_content)

    def extract_attributes(self, attribute="required", pop=True):
        """
        Extrahiert alle Vorkommen eines Attributs aus der kompletten YAML-Struktur.
        Durchläuft auch nach Fund eines Attributs weiter die tieferen Ebenen.

        Args:
            attribute (str): Name des zu extrahierenden Attributs
            pop (bool): Wenn True, wird das Attribut aus den Originaldaten entfernt

        Returns:
            dict: Verschachtelte Struktur mit allen gefundenen Attributen
        """

        def traverse_and_extract(data):
            result = {}

            if isinstance(data, dict):
                # Attribut im aktuellen Dictionary finden
                if attribute in data:
                    # Attribut gefunden, aber noch weitersuchen
                    result[attribute] = (
                        data.pop(attribute) if pop else data[attribute]
                    )

                # Rekursiv durch alle weiteren Schlüssel/Werte
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        extracted = traverse_and_extract(value)
                        if extracted:  # Nur nicht-leere Ergebnisse aufnehmen
                            result[key] = extracted

            elif isinstance(data, list):
                # Listen durchlaufen
                for i, item in enumerate(data):
                    extracted = traverse_and_extract(item)
                    if extracted:
                        result[i] = extracted

            return result if result else None

        return traverse_and_extract(self.content)


class ProjectConfigTemplate(YAMLConfigTemplate):
    def __init__(self, *args, **kw):
        super().__init__("project.yaml", *args, **kw)

    def render(
        self,
        inputpath=None,
        tei_directories=[],
        sourcepath=None,
        tei_directory=None,
        **kw,
    ):
        if sourcepath and tei_directory:
            tei_directories = find_tei_directory(sourcepath, tei_directory, 0)
        elif inputpath:
            tei_directories = inputpath.split(",")
        elif tei_directories:
            pass
        else:
            log.warning("Neither 'sourcepath' nor 'inputpath' is defined!")

        log.debug("tei_directories: %s" % tei_directories)

        # ToDo: merge the following code with the same code in
        # ProjectConfig.update
        subprojects = []
        unique_names = extract_unique_name(tei_directories)
        for p in tei_directories:
            prepared_path = prepare_path(p)
            splitted_pp = prepared_path.split("/")
            length = 3 if len(splitted_pp) >= 3 else len(splitted_pp)

            # Try to get a unique name for the subproject
            # 1. check if the name is in the list of unique names
            input_name = None
            for unique_name in unique_names:
                if unique_name in p:
                    input_name = unique_name
                    break
            # 2. if not, try to find a name in the path
            if not input_name:
                # 2.1 if sourcepath is given try to find name of subproject
                # only if there is more than one subproject
                if sourcepath:
                    if len(tei_directories) > 1:
                        input_name = find_name_of_subproject(
                            kw["projectname"], p, tei_directory
                        )
                    if len(tei_directories) <= 1 or not input_name:
                        input_name = sourcepath.split("/")[-1]
                # 2.2 if sourcepath is not given, use the last parts of path
                else:
                    input_name = "_".join(splitted_pp[-length:])

            outpath = prepare_path(
                (
                    kw["outputpath"]
                    if "outputpath" in kw and kw["outputpath"]
                    else self.projectpath
                ),
                subpath="/".join([input_name, "result"]),
                create=True,
            )

            basepath = prepare_path(
                self.projectpath,
                subpath=input_name,
                create=True,
            )

            subprojects.append(
                {
                    "inpath": prepared_path,
                    "name": input_name,
                    "outpath": outpath,
                    "basepath": basepath,
                    "files": sorted(get_files(prepared_path)),
                }
            )

        self.content["subprojects"] = subprojects

        OtherFiles(self.projectpath, None).init(self.content["project"])

        self.save()

        return ProjectConfig(projectpath=self.projectpath)


class CollectionConfigTemplate(YAMLConfigTemplate, CollectionMixin):
    def __init__(self, projectname=None, files=[], *args, **kw):
        self.projectname = projectname
        self.files = files
        super().__init__(
            "collection_template.yaml",
            *args,
            **kw,
        )
        self.project_config = ProjectConfig(self.projectpath)

    def _set_or_initialize_multi_items(
        self, collection_config, key, default_value
    ):
        current_value = getattr(collection_config, key)
        # Check if the collection configuration has content and the
        # current value is set
        if collection_config.content and current_value:
            # If both conditions are met, set the attribute to the current
            # value from the collection configuration
            setattr(self, key, current_value)
        else:
            # Otherwise, set the attribute to the provided default value
            setattr(self, key, default_value)

    def hits_in_files(self, xpath, ends_with=None):
        # all_sources = [self.base] + self.targets
        count = 0
        for tree in self.files:
            result = tree.find(xpath)
            if result is not None:
                if ends_with and not result.lower().endswith(ends_with):
                    continue
                count += 1
        if len(self.files) > 0:
            return round((count * 100) / len(self.files), 2)
        else:
            return 0

    def process_proposals(self, attribs, orig_content=None):

        for attrib in attribs:
            orig_attrib = None
            if orig_content:
                orig_attrib = orig_content.get(attrib)
            if attribs[attrib]:
                if "proposals" in attribs[attrib]:
                    attribs[attrib]["value"] = None
                    attribs[attrib]["xpath"] = None
                    # we pop out the 'proposals' and we want to remove them
                    # from the config eiterway
                    proposals = attribs[attrib].pop("proposals")
                    if not proposals:
                        continue

                    # init some statistics
                    min_hitrate = self.project_config.min_hitrate  # in %
                    winner = None
                    for _xpath_prop in proposals:
                        xpath_prop = split_xpath(_xpath_prop)
                        log.debug("[process_proposals] %s" % xpath_prop)
                        hitrate = self.hits_in_files(xpath_prop["xpath"])
                        if hitrate > min_hitrate:
                            winner = xpath_prop["full_path"]
                            min_hitrate = hitrate
                    if winner is not None and "xpath" in attribs[attrib]:
                        log.debug(
                            "[process_proposals] And the winner is `%s` having \
%s percent hitrate"
                            % (winner, min_hitrate)
                        )
                        attribs[attrib]["xpath"] = winner
                else:
                    # ok...there are no proposals at this level
                    # but maybe at the next level, so let's do some
                    # recursion
                    self.process_proposals(
                        attribs[attrib],
                        orig_content=orig_attrib,
                    )

    def render(self, overwrite=False):
        existing_config = CollectionConfig(self.subproject["basepath"])

        if (
            overwrite
            or not existing_config.content
            or not existing_config.short_title
        ):
            self.short_title = self.subproject["name"]
        else:
            self.short_title = existing_config.short_title

        if (
            overwrite
            or not existing_config.content
            or not existing_config.long_title
        ):
            if self.projectname:
                self.long_title = "%s - %s" % (
                    self.projectname,
                    self.subproject["name"],
                )

            else:
                self.long_title = self.short_title
        else:
            self.long_title = existing_config.long_title

        for target in self.subproject["files"]:
            self.elements.append(
                {"fullpath": target, "filename": target.split("/")[-1]}
            )

        # **WORK & EDITION**
        for section in ["attributes", "eltec_specs"]:
            # running through proposals and set xpath if hitrate is above
            self.process_proposals(
                self.collection[section],
                orig_content=(
                    None
                    if overwrite or not existing_config.content
                    else existing_config.collection[section]
                ),
            )

        # **BASIC CLASSIFICATIONS & GND_SUBJECTS**
        for subjects_item in [
            {
                "id": "basic_classifications",
                "default_url": "http://uri.gbv.de/terminology/bk/",
            },
            {
                "id": "gnd_subjects",
                "default_url": "https://d-nb.info/gnd/",
            },
        ]:
            self._set_or_initialize_multi_items(
                existing_config,
                subjects_item["id"],
                [
                    {
                        "id": {"xpath": None, "value": None},
                        "url": {
                            "xpath": None,
                            "value": subjects_item["default_url"],
                        },
                        "value": {"xpath": None, "value": None},
                    }
                ],
            )

        # **RIGHTS HOLDER & COLLECTOR**
        for admin_item in ["rights_holder", "collector"]:
            self._set_or_initialize_multi_items(
                existing_config,
                admin_item,
                [{"fullname": None, "url": None}],
            )

        # **IMAGES**
        # Check if there are any image proposals in the collection config
        image_xpaths = []
        # Iterate through proposed image XPaths from collection config
        for image_proposal in self.collection["images"].pop("proposals"):
            # Calculate hit rate for current image XPath,
            # checking file extensions
            hitrate = self.hits_in_files(
                image_proposal, ends_with=IMAGE_EXTENSIONS
            )
            self.project_config.min_hitrate
            # Add proposal if hit rate exceeds minimum and not already added
            if (
                hitrate > self.project_config.min_hitrate
                and image_proposal not in image_xpaths
            ):
                image_xpaths.append(image_proposal)
        # Set filtered image proposals as final image XPaths
        self.images = {"xpaths": image_xpaths}

        self.outname = "collection.yaml"
        self.save()

        log.info("%s initialized!" % self.path)
        return CollectionConfig(self.subproject["basepath"])
