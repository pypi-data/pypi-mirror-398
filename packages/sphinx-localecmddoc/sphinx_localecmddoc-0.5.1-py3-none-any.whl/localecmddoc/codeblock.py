"""Converting localecmddoc codeblocks to sphinx literal blocks,
thereby running the conde inside"""

from __future__ import annotations

import importlib
import io
import logging
import re

from docutils import nodes
from docutils.parsers.rst import Directive
from localecmd import CLI, Module
from localecmd.localisation import _
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.util.docutils import SphinxDirective

logger = logging.getLogger("localecmddoc")


def _get_modules(modules: dict[str, str]) -> list[Module]:
    """
    Get the localecmd mocules that should be documented.
    :param dict[str, str] modules: Python modules or localecmd modules
    to import as a localecmd.Module.
    Keys are python paths (for example 'localecmd.builtins'),
    values are corresponding name (for example 'core').
    The direct path to a localecmd.Module mayalso be given.
    In this case, the value (module name) is ignored as the module already has a name.
    :return: List of localecmd Modules
    :rtype: list[Module]
    :raises ValueError: If a modulename is empty

    """
    localecmd_modules = []

    # First use the modules that were given explicitly
    for module_path, module_name in modules.items():
        if not module_name:
            raise ValueError("Module name must not be empty!")
        try:
            # Try to import module and convert to localecmd.Module
            pymod = importlib.import_module(module_path)
            lcmdmod = Module.from_module(pymod, module_name)
            localecmd_modules.append(lcmdmod)

            msg = "Added converted py module {path} with name {name}."
            logger.debug(msg.format(path=module_path, name=module_name))

        except ModuleNotFoundError:
            # Import parent module and import the localecmd.Module directly
            module_path, _dot, varname = module_path.rpartition('.')
            pymod = importlib.import_module(module_path)
            lcmdmod = getattr(pymod, varname)
            lcmdmod.name = module_name
            localecmd_modules.append(lcmdmod)
            msg = f"Found localecmd.Module {lcmdmod.name!r} in {module_path!r}"
            logger.debug(msg)

    return localecmd_modules


def get_cli(app: Sphinx) -> CLI:
    """
    Get a localecmd.CLI for running commands or documenting modules.

    :param Sphinx app: Sphinx instance
    :return: command line interface. Remember to close this one before querying the next
    :rtype: CLI
    :raises ValueError: If a modulename is empty

    """

    modules = _get_modules(app.config.localecmd_modules)
    language = app.config.localecmd_codeblocks_language

    if language == 'sphinx':
        language = app.config.language
    if app.builder.name in ['gettext']:
        language = ''
    cli = CLI(modules, language, localedir=app.config.localecmd_localedir, stdout=io.StringIO())

    return cli


class LocalecmdExample(nodes.General, nodes.FixedTextElement):
    """This class exists to mark the block. It is later replaced"""

    pass


class LocalecmdExampleList(nodes.General, nodes.Element):
    "Mark a list of examples"

    pass


class LocalecmdExampleDirective(SphinxDirective):
    """
    Directive of localecmd examples.

    Type the commands only and sphinx will run the command and give the printout.
    """

    # this enables content in the directive
    has_content = True

    def run(self):
        docname = self.env.current_document.docname

        # If docname is within names that should be ignored, do nothing
        regexp = self.config.localecmd_ignore_codeblocks_in_files
        if regexp and re.match(regexp, docname):
            return []

        # Number, identification for this example
        targetnr = self.env.new_serialno('localecmd-example')
        targetid = f'localecmd-example-{targetnr}'
        # This is a reference to this example, so it is possible to come here
        targetnode = nodes.target('', '', ids=[targetid])

        code = '\n'.join(self.content).replace('"', r'\"').replace("'", r'\"')
        node = LocalecmdExample(code, code)  # rawsource, text
        node['translatable'] = True
        node['language'] = 'bash'

        # Add directive to list of examples
        if not hasattr(self.env, 'localecmddoc_all_examples'):
            self.env.localecmddoc_all_examples = {}
        if docname not in self.env.localecmddoc_all_examples:
            self.env.localecmddoc_all_examples[docname] = {}
        self.env.localecmddoc_all_examples[docname][self.lineno] = {
            'docname': self.env.current_document.docname,
            'line': self.lineno,
            'node': node,
            'target': targetnode,
        }
        # print(self.env.localecmddoc_all_examples)
        returnnodes = []
        if self.config.localecmd_target_codeblocks:
            returnnodes.append(targetnode)
        returnnodes.append(node)
        return returnnodes


class LocalecmdExampleListDirective(Directive):
    """
    Directive of localecmd examples list.
    """

    has_content = True

    def run(self):
        return [LocalecmdExampleList('')]


def clean_example_dicts(app: Sphinx, env: BuildEnvironment, docname: str):
    "Delete entries in the example dicts that are at wrong document????"
    if not hasattr(env, 'localecmddoc_all_examples'):
        return
    env.localecmddoc_all_examples = {
        d: x for d, x in env.localecmddoc_all_examples.items() if d != docname
    }


def merge_example_dicts(
    app: Sphinx, env: BuildEnvironment, docnames: list[str], other: BuildEnvironment
):
    if not hasattr(env, 'localecmddoc_all_examples'):
        env.localecmddoc_all_examples = {}  # type:ignore[attr-defined]

    if not hasattr(other, 'localecmddoc_all_examples'):
        return

    for docname, examples in other.localecmddoc_all_examples.items():
        if docname in env.localecmddoc_all_examples:  # type:ignore[attr-defined]
            raise RuntimeError("Must deeply merge examples!")
        else:
            env.localecmddoc_all_examples[docname] = examples  # type:ignore[attr-defined]


def process_code_blocks(app: Sphinx, doctree: nodes.document, docname: str):
    "Run code blocks and generate example list"
    run_codeblocks(app, doctree, docname)
    generate_example_list(app, doctree, docname)


def run_codeblocks(app: Sphinx, doctree: nodes.document, docname: str):
    "Run the code, get the output and put the result back into the node."
    if app.builder.name in ['gettext']:
        return
    cli = get_cli(app)

    for node in doctree.findall(LocalecmdExample):
        cli.transcript.new_entry()
        for line in node.astext().replace(r'\"', '"').split('\n'):
            cli.runcmd(line)
        txt = cli.transcript.get(-1)[0]

        newnode = nodes.literal_block(txt, txt)
        newnode['language'] = 'bash'
        node.replace_self(newnode)
        app.env.localecmddoc_all_examples[docname][node.line]['node'] = newnode  # type:ignore[attr-defined]
    cli.close()


def generate_example_list(app: Sphinx, doctree: nodes.document, docname: str):
    "Generate the list of all examples"

    if not hasattr(app.env, 'localecmddoc_all_examples'):
        return
    for node in doctree.findall(LocalecmdExampleList):
        content = []
        titletxt = _("Overview over localecmd code block examples")
        title = nodes.paragraph()
        title += nodes.rubric(titletxt, titletxt)
        content.append(title)
        for x_docname, x_dict in app.env.localecmddoc_all_examples.items():
            for x_line, x_info in x_dict.items():
                # Header
                fname = app.env.doc2path(x_docname, base=False)
                txt = _("Below code example block is on ")
                txtnode = nodes.Text(txt)

                # Reference
                reftxt = _("page {page}, line {line}").format(page=fname, line=x_line)
                refnode = nodes.reference(reftxt, reftxt)
                refnode['refdocname'] = x_info['docname']
                refnode['refuri'] = app.builder.get_relative_uri(docname, x_info['docname'])
                refnode['refuri'] += '#' + x_info['target']['refid']

                info = nodes.paragraph()
                info += txtnode
                info += refnode
                content.extend((info, x_info['node']))
        node.replace_self(content)
