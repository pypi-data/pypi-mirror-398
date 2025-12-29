#!/usr/bin/env python3

import pathlib
import tempfile
from io import StringIO

from babel.messages import Catalog
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from localecmd import create_pot
from localecmd.localisation import CLI_DOMAIN, FUNCTION_DOMAIN, TYPE_DOMAIN

from tests import samplemodule
from tests.test_all import build_sphinx, check_output_file

pytest_plugins = ('sphinx.testing.fixtures',)

index_en = """
# API of Commands

# Modules

* [Module core](core.md)
* [Module test](test.md)

The API was generated automatically with [sphinx-localecmddoc](https://codeberg.org/jbox/sphinx-localecmddoc/src/branch/main)

"""


def test_translation():
    with tempfile.TemporaryDirectory() as tmppath:
        tmpdir = pathlib.Path(tmppath)

        l1 = 'en_GB'
        l2 = 'to_TO'  # placeholder

        localedir = tmpdir / 'locale'
        localedir_l1 = localedir / l1 / 'LC_MESSAGES'
        localedir_l2 = localedir / l2 / 'LC_MESSAGES'
        localedir_l1.mkdir(parents=True)
        localedir_l2.mkdir(parents=True)

        conf = {
            'language': l1,
            'source_suffix': {'.md': 'markdown'},
            'extensions': ['myst_parser', 'localecmddoc'],
            'myst_enable_extensions': ["fieldlist", "colon_fence"],
            # 'localecmd_searchmodules': ['package'],
            'localecmd_modules': {
                'localecmd.builtins': 'core',
                'package.module': 'test',
            },
            'localecmd_outdir': '',
            'localecmd_codeblocks_language': 'sphinx',
            'localecmd_localedir': str(localedir),
            'localecmd_target_codeblocks': False,
            'locale_dirs': [str(localedir)],
        }
        # Extract strings
        create_pot(
            [samplemodule.module],
            str(localedir),
            project='localecmddoc-test',
            include_builtins=True,
        )
        # Now the same for sphinx
        build_sphinx(tmpdir, conf, 'gettext', localedir)
        for file in (localedir / 'gettext').iterdir():
            file.replace(localedir / file.name)
        # Initialise translations
        cli_domains = [CLI_DOMAIN, FUNCTION_DOMAIN, TYPE_DOMAIN]
        sphinx_domains = ['core', 'index', 'test']
        for domain in cli_domains + sphinx_domains:
            file = localedir / (domain + '.pot')
            txt = StringIO(file.read_text('utf8'))
            catalog = read_po(txt, None, domain)

            catalog_l1 = Catalog(l1, domain)
            catalog_l2 = Catalog(l2, domain)
            # Translate
            for message in catalog:
                catalog_l1.add(message.id, message.id, context=message.context)
                catalog_l2.add(message.id, message.id.lower(), context=message.context)

            with open(localedir_l1 / (domain + '.mo'), 'wb') as file:
                write_mo(file, catalog_l1)
            with open(localedir_l2 / (domain + '.mo'), 'wb') as file:
                write_mo(file, catalog_l2)

        # Check that it worked
        app = build_sphinx(tmpdir, conf, 'markdown', tmpdir / l1)
        app.cleanup()
        conf['language'] = l2
        status = StringIO()
        build_sphinx(
            tmpdir, conf, 'markdown', tmpdir / l2, status=status, warning=status, verbosity=2
        )

        check_output_file(tmpdir / l1 / 'markdown' / 'index.md', index_en)
        check_output_file(tmpdir / l2 / 'markdown' / 'index.md', index_en.lower())

        check_output_file(
            tmpdir / l2 / 'markdown' / 'test.md', samplemodule.expected_output_built_md_lower
        )
        check_output_file(
            tmpdir / l1 / 'markdown' / 'test.md', samplemodule.expected_output_built_md
        )
