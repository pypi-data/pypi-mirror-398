#!/usr/bin/env python3
""" """

from __future__ import annotations

import inspect
import pathlib
import shutil
import sys
import tempfile
from typing import Any

import pytest
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.testing.util import SphinxTestApp

from tests import examplelist, samplemodule


def build_sphinx(
    path: pathlib.Path,
    conf: dict[str, Any],
    builder: str = 'markdown',
    builddir: pathlib.Path | None = None,
    **kwargs,
) -> Sphinx:
    srcdir = path / 'src'
    pkgdir = srcdir / 'package'
    docdir = path / 'docs'

    # Create directories
    srcdir.mkdir(exist_ok=True)
    pkgdir.mkdir(exist_ok=True)
    docdir.mkdir(exist_ok=True)

    # Add path to sys.path to be able to find the package with out module
    sys.path.append(str(srcdir))

    # Create source files
    (pkgdir / '__init__.py').write_text(inspect.getsource(samplemodule), 'utf8')

    # Create configutation file
    (docdir / 'conf.py').write_text(str(conf))

    app = SphinxTestApp(builder, docdir, builddir, confoverrides=conf, **kwargs)
    app.build()
    return app


def check_output_file(filename: pathlib.Path, content: str):
    assert content.strip() == filename.read_text('utf8').strip()


def test_autodoc():
    with tempfile.TemporaryDirectory() as tmppath:
        tmpdir = pathlib.Path(tmppath)

        conf = {
            'language': 'en',
            'source_suffix': {'.md': 'markdown'},
            'extensions': ['myst_parser', 'localecmddoc'],
            'myst_enable_extensions': ["fieldlist", "colon_fence"],
            'localecmd_modules': {
                'localecmd.builtins': 'core',
                'package.module': 'test',
            },
            'localecmd_outdir': '',
            'localecmd_codeblocks_language': '',
            'localecmd_target_codeblocks': False,
        }
        # Expected outputs
        expected_indexfile = inspect.cleandoc("""
        # API of Commands

        # Modules
        
        * [Module core](core.md)
        * [Module test](test.md)
        
        The API was generated automatically with [sphinx-localecmddoc](https://codeberg.org/jbox/sphinx-localecmddoc/src/branch/main)

        """)
        app = build_sphinx(tmpdir, conf)

        check_output_file(app.outdir / 'index.md', expected_indexfile)
        assert (app.outdir / 'core.md').exists()
        check_output_file(app.outdir / 'test.md', samplemodule.expected_output_built_md)
        # Good, now remove output for next tests
        shutil.rmtree(app.outdir)

        # Remove builtin commands and check that core.md is removed.
        # Also load the module directly
        conf['localecmd_modules'].pop('localecmd.builtins')
        conf['localecmd_modules']['package.module'] = 'package'
        app = build_sphinx(tmpdir, conf)

        # check_output_file(app.outdir / 'index.md', expected_indexfile)
        assert not (app.outdir / 'core.md').exists()
        check_output_file(app.outdir / 'package.md', samplemodule.expected_output_package)
        shutil.rmtree(app.outdir)

        # Cant have empty module names
        conf['localecmd_modules']['package.module'] = ''
        with pytest.raises(ExtensionError):
            app = build_sphinx(tmpdir, conf)


def test_examplelist(tmp_path):
    tmpdir = pathlib.Path(tmp_path)
    filename = 'index.md'
    (tmpdir / 'docs').mkdir()
    (tmpdir / 'docs' / filename).write_text(examplelist.exampletext)
    print(*tmpdir.iterdir())
    conf = {
        'language': 'en',
        'source_suffix': {'.md': 'markdown'},
        'extensions': ['myst_parser', 'localecmddoc'],
        'myst_enable_extensions': ["fieldlist", "colon_fence"],
        'localecmd_modules': {
            'localecmd.builtins': 'core',
        },
        'localecmd_outdir': 'functions',
        'localecmd_codeblocks_language': '',
    }
    app = build_sphinx(tmpdir, conf)
    check_output_file(app.outdir / filename, examplelist.examplelist_output)


def test_ignoredirs(tmp_path):
    tmpdir = pathlib.Path(tmp_path)
    filename = 'index.md'
    (tmpdir / 'docs').mkdir()
    (tmpdir / 'docs' / filename).write_text(examplelist.exampletext)
    print(*tmpdir.iterdir())
    conf = {
        'language': 'en',
        'source_suffix': {'.md': 'markdown'},
        'extensions': ['myst_parser', 'localecmddoc'],
        'myst_enable_extensions': ["fieldlist", "colon_fence"],
        'localecmd_modules': {
            'localecmd.builtins': 'core',
        },
        'localecmd_outdir': 'functions',
        'localecmd_codeblocks_language': '',
        'localecmd_ignore_codeblocks_in_files': '^',
    }
    app = build_sphinx(tmpdir, conf)
    check_output_file(app.outdir / filename, '')
