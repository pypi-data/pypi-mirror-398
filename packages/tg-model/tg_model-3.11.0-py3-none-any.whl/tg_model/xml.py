# -*- coding: utf-8 -*-
# Copyright (C) 2023-2024 TUD | ZIH
# ralf.klammer@tu-dresden.de

import logging

import re
import requests

from copy import deepcopy
from lxml.etree import fromstring, ElementTree, tostring

log = logging.getLogger(__name__)


class XMLParserBase(object):

    def __init__(self, uri=None, tree=None, default_ns_prefix="tei"):
        self.uri = uri
        self.default_ns_prefix = default_ns_prefix
        self.tree = tree
        self.load_resource()

    def __repr__(self):
        return "<XSDParserBase: %s>" % self.uri

    @property
    def file_name(self):
        if self.uri:
            return self.uri.split("/")[-1]

    def load_resource(self):
        log.debug("XMLParserBase - load uri: %s" % self.uri)
        try:
            if self.tree is None:
                if self.uri.startswith("http"):
                    resource = requests.get(self.uri).content
                else:
                    with open(self.uri, "r", encoding="utf-8") as file:
                        resource = file.read()
                resource = resource.replace("\t", "  ").encode()
                self.tree = fromstring(resource)
        except Exception as e:
            log.error(e)
            raise "Unable to load XML resource"

    def _add_default_prefix(self, search_string):
        log.debug("_add_default_prefix")
        log.debug(f"before: {search_string}")

        # find all urls in search_string and replace them with a placeholder
        url_regex = r'(?<=\{)(https?://[^}]+)(?=\})|(?<=")(https?://[^"]+)(?=")|(?<=@{)(http[^}]+)(?=\})'
        urls_found = re.findall(url_regex, search_string)
        urls = [url for match in urls_found for url in match if url]
        for url in urls:
            search_string = search_string.replace(url, "preservedurls")

        if search_string.find("//") != -1:
            # remove all double slashes to avoid hitting them also in
            # the next step
            search_string = search_string.replace("//", "^^")
        if search_string.find("/@") != -1:
            # remove all 'key requests' to avoid hitting them also in
            # the next step
            search_string = search_string.replace("/@", "^@^")
        # replace all '/' with '/prefix:'
        search_string = search_string.replace(
            "/", f"/{self.default_ns_prefix}:"
        )
        # bring back double slashes and add prefix
        search_string = search_string.replace(
            "^^", f"//{self.default_ns_prefix}:"
        )
        # bring back 'key requests'
        search_string = search_string.replace("^@^", "/@")

        # replace all preservedurls with the original urls
        for i in range(0, len(urls)):
            search_string = search_string.replace("preservedurls", urls[i], 1)

        if search_string.startswith(".//"):
            search_string = search_string[1:]

        log.debug(f"after: {search_string}")

        return search_string

    @property
    def namespaces(self):
        ns = self.tree.nsmap.copy()
        if None in ns:
            ns[self.default_ns_prefix] = ns.pop(None)
        return ns

    def find(
        self, search_string, elem=None, get_node=False, node_as_text=False
    ):
        search_string = self._add_default_prefix(search_string)
        result = (elem if elem is not None else self.tree).xpath(
            search_string, namespaces=self.namespaces
        )
        if len(result) > 0:
            result = deepcopy(result[0])
        else:
            result = None
        if get_node:
            return result
        elif node_as_text:
            return tostring(result)
        elif isinstance(result, str):
            return result.rstrip()
        elif result is not None and result.text is not None:
            return result.text.rstrip()
        else:
            log.warning("Nothing found for %s in %s!" % (search_string, self))

    def findall(
        self,
        search_string,
        elem=None,
        exclude_empty_text=False,
        text=None,
    ):
        search_string = self._add_default_prefix(search_string)

        nodes = (elem if elem is not None else self.tree).xpath(
            search_string, namespaces=self.namespaces
        )

        if text:
            return [node for node in nodes if node.text == text]

        results = []
        for node in nodes:
            if isinstance(node, str):
                results.append(node.rstrip())
            elif node.text is not None:
                results.append(node.text.rstrip())
            # check if there is only one child with text
            elif len([c for c in node.getchildren() if c.text]) == 1:
                # use the first child with text
                results.append(
                    [c for c in node.getchildren() if c.text][0].text.strip()
                )
            else:
                if not exclude_empty_text:
                    results.append("")
                log.warning(
                    "Nothing found for %s in %s!" % (search_string, self)
                )
        return results

    def write(self, filename):
        ElementTree(self.tree).write(
            filename, pretty_print=True, encoding="utf-8"
        )

    def print_tree(self):
        return tostring(self.tree).decode("utf-8")
