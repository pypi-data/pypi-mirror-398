# -*- coding: utf-8 -*-
# Copyright (C) 2025 TUD | ZIH
# ralf.klammer@tu-dresden.de
import logging

from os import path, remove
from shutil import copyfile

from tgadmin.tgimport import TGimport
from tgclients import (
    TextgridConfig,
    TextgridCrud,
    TextgridSearch,
)
from tgclients.config import PROD_SERVER, TEST_SERVER

from .util import prepare_path, RenderBase

log = logging.getLogger(__name__)


class OtherFiles(RenderBase):
    dummy_avatar = "avatar.png"
    dummy_xslt = "dummy.xslt"
    subpath = "other_files"

    def __init__(self, projectpath, project_config, *args, **kwargs):
        super().__init__(projectpath, *args, **kwargs)
        self.projectpath = projectpath
        self.project_config = project_config
        self._avatar = False
        self._xslt = False
        self._collectors = None
        self.facets = {}
        self._contents = None

    @property
    def contents(self):
        if self._contents is None:
            self._contents = {
                "portalconfig": {
                    "filename": "portalconfig.xml",
                    "mime": "text/tg.portalconfig+xml",
                },
                "readme": {
                    "filename": "README.md",
                    "mime": "text/markdown",
                },
            }
            for key, value in self._contents.items():
                value["path"] = path.join(self.projectpath, value["filename"])

            if self.xslt:
                self._contents["xslt"] = {
                    "filename": self.xslt,
                    "mime": "application/xslt+xml",
                }
            if self.avatar:
                self._contents["avatar"] = {
                    "filename": self.avatar,
                    "mime": f"image/{self.avatar.split('.')[-1]}",
                }
            for value in self._contents.values():
                if "path" not in value:
                    value["path"] = path.join(
                        self.projectpath, "other_files", value["filename"]
                    )
        return self._contents

    def init(
        self,
        config,
        include_dummy_avatar=True,
        include_dummy_xslt=False,
    ):
        # create directory 'other_files'
        other_files_path = prepare_path(
            self.projectpath, subpath=self.subpath, create=True
        )

        # set default avatar & xslt (if requested)
        config["avatar"] = self.dummy_avatar if include_dummy_avatar else None
        config["xslt"] = self.dummy_xslt if include_dummy_xslt else None

        # copy avatar.png & dummy.xslt to the directory 'other_files'
        dummies = []
        if include_dummy_avatar:
            dummies.append(self.dummy_avatar)
        if include_dummy_xslt:
            dummies.append(self.dummy_xslt)
        for filename in dummies:
            destination = path.join(other_files_path, filename)
            if not path.exists(destination):
                copyfile(
                    # source
                    path.join(path.dirname(__file__), "templates", filename),
                    destination,
                )

    def add_facets(self, facets):
        for key in facets:
            if key in self.facets:
                self.facets[key] += facets[key]
            else:
                self.facets[key] = facets[key]

    def remove_dummy_avatar(self):
        avatar_path = path.join(
            self.projectpath, self.subpath, self.dummy_avatar
        )
        if path.exists(avatar_path):
            remove(avatar_path)

    def remove_dummy_xslt(self):
        xslt_path = path.join(self.projectpath, self.subpath, self.dummy_xslt)
        if path.exists(xslt_path):
            remove(xslt_path)

    def exists(self, filename):
        return path.exists(path.join(self.projectpath, self.subpath, filename))

    @property
    def avatar(self):
        if self._avatar is False:
            avatar = self.project_config.get("avatar", "project")

            if avatar is None:
                # avatar is not defined at all -> unset
                self.remove_dummy_avatar()
                self._avatar = None
            else:
                # avatar is defined -> check if it is the default avatar
                if avatar.endswith(self.dummy_avatar):
                    # avatar is the default avatar -> set default avatar
                    self._avatar = avatar
                else:
                    # avatar is not the default avatar -> remove default avatar
                    self.remove_dummy_avatar()
                    if self.exists(avatar):
                        # individual avatar file exists -> set avatar
                        self._avatar = avatar
                    else:
                        # individual avatar file does not exist -> unset
                        self._avatar = None

        return self._avatar

    def get_avatar(self):
        if self.avatar:
            self.render_meta_file(
                self.avatar,
                f"image/{self.avatar.split('.')[-1]}",
                subpath=self.subpath,
            )
            return path.join(self.subpath, self.avatar)

    def get_xslt(self):
        if self.xslt:
            self.render_meta_file(
                self.xslt,
                "application/xslt+xml",
                subpath=self.subpath,
            )
            return path.join(self.subpath, self.xslt)

    @property
    def xslt(self):
        if self._xslt is False:
            xslt = self.project_config.get("xslt", "project")

            if xslt is None:
                # xslt is not defined at all -> unset
                self.remove_dummy_xslt()
                self._xslt = None
            else:
                # xslt is defined -> check if it is the default xslt
                if xslt.endswith(self.dummy_xslt):
                    # xslt is the default xslt -> set default xslt
                    self._xslt = xslt
                else:
                    # xslt is not the default xslt -> remove default xslt
                    self.remove_dummy_xslt()
                    if self.exists(xslt):
                        # individual xslt file exists -> set xslt
                        self._xslt = xslt
                    else:
                        # individual xslt file does not exist -> unset
                        self._xslt = None
        return self._xslt

    @property
    def collectors(self):
        if self._collectors is None:
            self._collectors = self.project_config.get(
                "collectors", "project", default=[]
            )
            if not [c for c in self._collectors if c["name"]]:
                raise Exception("No collectors defined in project.yaml")
        return self._collectors

    @property
    def collection_base(self):
        _collection = {
            "filename": f"{self.subpath}.collection",
            "mime": "text/tg.collection+tg.aggregation+xml",
        }
        _collection["path"] = path.join(
            self.projectpath, _collection["filename"]
        )
        return _collection

    def render_collection_base(self):
        files = []
        for file in [self.get_xslt(), self.get_avatar()]:
            if file is not None:
                files.append(file)
        self.render(
            self.collection_base["path"],
            {
                "title": self.subpath,
                "other_files": files,
            },
            "{{ collection }}.collection",
        )
        self.render_meta_file(
            title="other files",
            template="{{ collection }}.collection.meta",
            **self.collection_base,
        )

    def render_all(self):
        self.render_collection_base()
        self.render_portalconfig()
        self.render_readme()

    def render_portalconfig(self):
        rendered = self.render(
            self.contents["portalconfig"]["path"],
            {
                "facets": self.facets,
                "title": self.project_config.get("title", "project")
                or "Set title of your project",
                "description": self.project_config.get(
                    "description", "project"
                )
                or "Set description of your project",
                "avatar": self.get_avatar(),
                "xslt": self.get_xslt(),
            },
            self.contents["portalconfig"]["filename"],
            skip_if_exists=True,
        )
        if rendered:
            self.render_meta_file(**self.contents["portalconfig"])

    def render_readme(self):
        rendered = self.render(
            self.contents["readme"]["path"],
            {},
            self.contents["readme"]["filename"],
            skip_if_exists=True,
        )
        if rendered:
            self.render_meta_file(**self.contents["readme"])

    def render_meta_file(
        self,
        filename=None,
        mime=None,
        title=None,
        subpath=None,
        template="{{ file }}.meta",
        **kwargs,
    ):
        meta_filename = f"{filename}.meta"
        _path = (
            path.join(self.projectpath, subpath)
            if subpath
            else self.projectpath
        )
        self.render(
            path.join(_path, meta_filename),
            {
                "filename": filename,
                "title": filename if title is None else title,
                "format": mime,
                "collectors": self.collectors,
            },
            template,
        )

    def get_all_files(self):
        return [of["filename"] for of in self.contents.values()]

    @property
    def imex_path(self):
        return path.join(self.projectpath, "other_files.imex")

    def remove_imex_file(self):
        if path.exists(self.imex_path):
            remove(self.imex_path)

    def upload(self, tg_session_id, tg_project_id, tg_server):
        log.debug(
            f"Uploading other files ({self.projectpath}): %s, %s, %s"
            % (tg_session_id, tg_project_id, tg_server)
        )
        files = [self.contents[c]["path"] for c in ["portalconfig", "readme"]]
        files.append(self.collection_base["path"])

        self.render_all()

        config = TextgridConfig(
            PROD_SERVER if tg_server == "live" else TEST_SERVER
        )
        crud = TextgridCrud(config)

        tg_importer = TGimport(
            tg_session_id,
            crud,
            project_id=tg_project_id,
            ignore_warnings=True,
            imex_location=self.imex_path,
        )
        tg_importer.upload(filenames=files)
