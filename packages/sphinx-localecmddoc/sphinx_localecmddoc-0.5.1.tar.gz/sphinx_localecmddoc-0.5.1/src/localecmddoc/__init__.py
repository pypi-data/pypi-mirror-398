#!/usr/bin/env python3
"""
Sphinx extension to generate documentation of localecmd modules.

This module contains the connections with sphinx.
"""

from __future__ import annotations

import pathlib

from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.typing import ExtensionMetadata

from localecmddoc.autodoc import write_module_docs
from localecmddoc.codeblock import (
    LocalecmdExampleDirective,
    LocalecmdExampleListDirective,
    clean_example_dicts,
    get_cli,
    merge_example_dicts,
    process_code_blocks,
)

version = '0.1'  ## Old.  todo: update from pyproject.toml

logger = logging.getLogger("localecmddoc")


def create_docs(app: Sphinx):
    output_folder = pathlib.Path(app.srcdir) / app.config.localecmd_outdir

    cli = get_cli(app)
    logger.debug("[localecmddoc] Create files with in-program documentation")
    write_module_docs(cli.modules, output_folder, remove_pycode=True)
    cli.close()


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value(
        'localecmd_modules',
        {'localecmd.builtins': 'core'},
        'html',
        dict[str, str],
        "Pairs of module paths to load as localecmd.Module and their name",
    )
    app.add_config_value(
        'localecmd_outdir',
        'functions',
        'html',
        str,
        "Directory for output of the command docs. Relative to sphinx output dir",
    )
    app.add_config_value(
        'localecmd_remove_python_code_blocks',
        True,
        'html',
        bool,
        "If python code blocks should be removed from docstrings",
    )
    app.add_config_value(
        'localecmd_target_codeblocks',
        True,
        'html',
        bool,
        "If localecmd example code blocks should get target attributes",
    )
    app.add_config_value(
        'localecmd_ignore_codeblocks_in_files',
        '',
        'html',
        str,
        'Regular expression of file names where lcmd-example'
        'codeblocks should not be run or displayed',
    )
    app.add_config_value(
        'localecmd_codeblocks_language',
        'sphinx',
        'html',
        str,
        "What language to use for the CLI in and outputs. "
        "Default is 'sphinx', same as 'language' setting",
    )
    app.add_config_value(
        'localecmd_localedir',
        'locale',
        'html',
        str,
    )

    app.add_directive('lcmd-example', LocalecmdExampleDirective)
    app.add_directive('lcmd-examplelist', LocalecmdExampleListDirective)

    app.setup_extension('myst_parser')

    app.connect("builder-inited", create_docs)
    app.connect('env-purge-doc', clean_example_dicts)
    app.connect('env-merge-info', merge_example_dicts)
    app.connect("doctree-resolved", process_code_blocks)

    return {
        'version': version,
        'env_version': 1,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
