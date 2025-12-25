# -*- coding: utf-8 -*-
# Copyright (C) 2023-2024 TUD | ZIH
# ralf.klammer@tu-dresden.de

import logging

import click  # type: ignore

from .project import Project
from .util import cli_startup, prepare_path
from .tei import TEIParser
from .yaml import (
    ProjectConfig,
    ProjectConfigTemplate,
    CollectionConfigTemplate,
)

log = logging.getLogger(__name__)


def _init_ctx(ctx, debug, **kw):
    cli_startup(log_level=debug and logging.DEBUG or logging.INFO)
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug

    log.info("Projectname: %s" % kw["projectname"])

    kw["basepath"] = prepare_path(kw["basepath"])
    log.info("General projects path: %s" % kw["basepath"])

    kw["projectpath"] = prepare_path(
        "{basepath}/{projectname}".format(**kw), create=True
    )
    log.info("Project path: %s" % kw["projectpath"])

    if "inputpath" in kw:
        kw["inputpath"] = prepare_path(
            kw["inputpath"].format(**kw), create=True
        )
        log.info("Input path: %s" % kw["inputpath"])

    ctx.obj.update(kw)


@click.group()
@click.option("--debug/--no-debug", "-d", is_flag=True, default=False)
@click.option("--projectname", "-n", required=True, help="name of project")
@click.option(
    "--basepath",
    "-b",
    default="./projects",
    help="basic path for all projects",
)
@click.pass_context
def tg_model(ctx, **kw):
    """
    This is an approach on building a fluffy "datamodel" for a TextGrid-ingest
    """
    _init_ctx(ctx, **kw)


@tg_model.command()
@click.pass_context
@click.option("--templates", help="path to individual templates")
@click.option(
    "--no_validation", help="Do not validation", is_flag=True, default=False
)
@click.option(
    "--no_export", help="Do not export CSV", is_flag=True, default=False
)
def build_collection(
    ctx, templates=None, no_export=None, no_validation=None, **kw
):
    pm = Project(ctx.obj["projectpath"], templates=templates)
    pm.render_project(validate=not no_validation, export=not no_export)


@click.option(
    "--no_validation", help="Do not validation", is_flag=True, default=False
)
@click.option(
    "--no_export", help="Do not export CSV", is_flag=True, default=False
)
@tg_model.command()
@click.pass_context
@click.option("--templates", help="path to individual templates")
def run(ctx, templates=None, no_export=None, no_validation=None, **kw):
    pm = Project(ctx.obj["projectpath"], templates=templates)
    pm.render_project(validate=not no_validation, export=not no_export)


@tg_model.command()
@click.pass_context
def export(ctx, **kw):
    pm = Project(ctx.obj["projectpath"])
    pm.export()


@tg_model.command()
@click.pass_context
def validate(ctx, templates=None, **kw):
    # CollectionConfigTemplate(**ctx.obj)
    # rprint(CollectionConfigTemplate(**ctx.obj).extracted_comments)
    # rprint(CollectionConfigTemplate(**ctx.obj).extracted_requirements)
    # rprint(
    #     CollectionConfigTemplate(**ctx.obj).extract_attributes(
    #         attribute="required"
    #     )
    # )

    pm = Project(ctx.obj["projectpath"], templates=templates)
    pm.validate()


@click.group()
@click.option("--debug/--no-debug", "-d", is_flag=True, default=False)
@click.option("--projectname", "-n", required=True, help="path to project")
@click.option(
    "--basepath",
    "-b",
    default="./projects",
    help="path to project",
    show_default=True,
)
@click.option(
    "--outputpath",
    "-o",
    help="path to the final outputs | defaults to subpath of input within projectsfolder",
)
@click.pass_context
def tg_configs(ctx, **kw):
    _init_ctx(ctx, **kw)


def _build_project_config(ctx, **kw):
    kw.update(ctx.obj)

    project_config = ProjectConfig(ctx.obj["projectpath"])

    if not project_config.exists():
        project_config = ProjectConfigTemplate(ctx.obj["projectpath"]).render(
            **kw
        )
    else:
        project_config.update(**kw)

    log.info("*" * 50)
    log.info("%s/project.yaml initialized!" % ctx.obj["projectpath"])
    log.info("*" * 50)

    request = project_config.validate()
    if request:
        log.warning("###Validation failed###")
        for r in request:
            log.warning(r)


@tg_configs.command()
@click.pass_context
@click.option(
    "--inputpath",
    "-i",
    help="Path(-s) to directory containing TEI-documents, can be one or multiple (separated by `,`)",
)
@click.option(
    "--sourcepath",
    "-s",
    help="This is the basic path of the data source.",
)
@click.option(
    "--tei_directory",
    "-t",
    default="tei",
    help="This is the name of the directory where the TEI documents are located. (default='tei')",
)
def project(ctx, **kw):
    """
    Creating project config and subproject directories

    You have 2 options:
    Either you set the concrete path ("inputpath") to one or more
    (comma separated) directories containing TEI documents.
    Or you set the "sourcepath" and the name of the directory
    ("tei_directory"), where the TEI documents are located. And the concrete
    path will be analysed automatically!
    e.g.: tg_configs project -n my_project -i /path/to/tei_docs
    """
    _build_project_config(ctx, **kw)


def _build_collection_config(ctx, subproject, overwrite):
    CollectionConfigTemplate(
        subproject=subproject,
        files=[TEIParser(fullpath=file) for file in subproject["files"]],
        **ctx.obj,
    ).render(overwrite=overwrite)


@tg_configs.command()
@click.pass_context
@click.option(
    "--overwrite", "-o", is_flag=True, help="Overwrite already defined values."
)
def collection(ctx, overwrite):
    """
    Creating collection config and subproject directorys
    e.g.: tg_configs collection -n my_project
    """
    project_config = ProjectConfig(ctx.obj["projectpath"])
    log.info("*" * 50)
    for subproject in project_config.content["subprojects"]:
        _build_collection_config(ctx, subproject, overwrite)
    log.info("Edit it/them and run 'tg_model build-collection' afterwards")
    log.info("*" * 50)


@tg_configs.command()
@click.pass_context
@click.option(
    "--inputpath",
    "-i",
    help="Path(-s) to directory containing TEI-documents, can be one or multiple (separated by `,`)",
)
@click.option(
    "--sourcepath",
    "-s",
    help="This is the basic path of the data source.",
)
@click.option(
    "--tei_directory",
    "-t",
    default="tei",
    help="This is the name of the directory where the TEI documents are located. (default='tei')",
)
@click.option("--overwrite", "-o", is_flag=True)
def all(ctx, overwrite, **kw):
    """
    Creating all configs and subproject directories at once

    You have 2 options:
    Either you set the concrete path ("inputpath") to one or more
    (comma separated) directories containing TEI documents.
    Or you set the "sourcepath" and the name of the directory
    ("tei_directory"), where the TEI documents are located. And the concrete
    path will be analysed automatically!
    e.g.: tg_configs all -n my_project -i /path/to/tei_docs
    """
    _build_project_config(ctx, **kw)
    project_config = ProjectConfig(ctx.obj["projectpath"])
    for subproject in project_config.content["subprojects"]:
        _build_collection_config(ctx, subproject, overwrite)


if __name__ == "__main__":
    project(obj={})
