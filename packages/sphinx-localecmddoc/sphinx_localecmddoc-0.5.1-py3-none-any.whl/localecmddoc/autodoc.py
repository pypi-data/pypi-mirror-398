#!/usr/bin/env python3
"""
Functions for creating automatic documentation of localecmd.Modules.
"""

from __future__ import annotations

import inspect
import pathlib
import re
from typing import Iterable

from jinja2 import Template
from localecmd import Function, Module
from localecmd.func import BRAILLE_PATTERN_BLANK
from localecmd.localisation import d_, f_
from localecmd.topic import Topic
from sphinx.util import logging

logger = logging.getLogger("localecmddoc")

INDEX_TEMPLATE = Template("""
# API of Commands

```{toctree}
:caption: Modules
:titlesonly:
    
{% for filename in module_files %}

{{ filename }}.md
{% endfor %}
```

The API was generated automatically with [sphinx-localecmddoc](https://codeberg.org/jbox/sphinx-localecmddoc/src/branch/main)

""")


def write_module_docs(
    modules: Iterable[Module],
    output_folder: pathlib.Path,
    file_extension: str = '.md',
    *,
    remove_pycode: bool = True,
):
    """
    Write the files with the Modules documentation to disk.

    :::{attention}
    Use a dedicated output folder.
    The files within the output folder that do not belong to the docs will be deleted.
    :::

    :param Iterable[Module] modules: Modules to write the docs for.
    :param pathlib.Path output_folder: Into which folder to write the files.
    If not existing, this folder will be created.
    :param str, optional file_extension: File extension of output files. Default is '.md'
    :param bool remove_pycode: If Python code blocks should be removed from the output.

    """

    written_files = []

    # Ensure that destination folder is empty.
    output_folder.mkdir(exist_ok=True)
    logger.info(f"[localecmddoc] Created folder {output_folder}")

    # Write modules
    for module in modules:
        txt = create_module_doc_output(module, remove_pycode=remove_pycode)
        output_file = output_folder / (module.name + file_extension)
        write_file(output_file, txt)
        written_files.append(output_file)

    # Write index file
    output_file = output_folder / ('index' + file_extension)
    txt = INDEX_TEMPLATE.render(module_files=[module.name for module in modules])
    write_file(output_file, txt)
    written_files.append(output_file)

    # Clear files in this folder that were not written to
    logger.debug(f"[localecmddoc] Delete old files in {output_folder}")
    for path in output_folder.iterdir():
        if path not in written_files and path.is_file():
            path.unlink()
            logger.debug(f"[localecmddoc] Deleted file {path}")


def write_file(file: pathlib.Path, txt: str):
    """
    Write txt to file if the file does not contain this text already.
    """
    if not file.exists() or file.read_text('utf8') != txt:
        logger.info(f"[localecmddoc] Writing to {file.name}")
        file.write_text(txt, 'utf8')
    else:
        logger.debug(f"[localecmddoc] File {file.name} is left unchanged")


def create_module_doc_output(module: Module, *, remove_pycode: bool) -> str:
    """
    Create a string of all docstrings within the module in markdown format.

    :param Module module: The module to create the documentation for
    :param bool remove_pycode: If Python code blocks should be removed from the output.

    """
    # Actual work: Printing docstrings
    txt = ''
    txt += "# Module " + module.name + "\n"
    txt += str(inspect.getdoc(module))
    txt += "\n\n"
    # Should print overview of functions here
    directive = "{py:function}"

    for topic in module.topics:
        txt += getdoc_topic(topic, directive)
    for cmd in module.functions:
        txt += getdoc_cmd(cmd, directive, remove_pycode=remove_pycode)
    return txt


def fill_md_directive(directive: str, content: str, arg: str) -> str:
    "Set up directive with given properties"
    fence = '`' * 3
    while fence in content:
        fence += '`'
    txt = f"{fence}{directive} {arg}\n\n{content}\n{fence}\n"
    return txt


def getdoc_topic(topic: Topic, directive: str) -> str:
    "Get docstring from Topic and translate it to markdown"
    doc = str(inspect.getdoc(topic))
    txt = fill_md_directive(directive, doc, topic.name.capitalize())
    return txt


def getdoc_cmd(cmd: Function, directive: str, *, remove_pycode: bool) -> str:
    """
    Get docstring from Function and translate it to markdown.

    :param Function cmd: Function containing the docstring
    :param str directive: Sphinx directive to use for the resulting documentation.
    :param bool remove_pycode: If Python code blocks should be removed from the output.
    """
    body = cmd.doc
    body = translate_parameters(cmd.doc, cmd.fullname)

    remove_arg_names = cmd.parameters[: len(cmd.prependargs)] + list(cmd.addkwargs.keys())
    for arg in remove_arg_names:
        body = remove_injected_argument(body, arg)
    if remove_pycode:
        body = remove_python_code_blocks(body)

    title = cmd.calling
    if ' ' not in title:
        title += BRAILLE_PATTERN_BLANK
    txt = fill_md_directive(directive, body, title)
    return txt


def translate_parameters(s: str, fullname: str = ""):
    """
    Translate parameters and types in the parameters section of a doctring

    Docstring must be sphinx-style

    :param str s: docstring to translate
    :type s: str
    :param str fullname: Full name of function. Used to call
    {py:func}`~zfp.cli.localisation.f_`. defaults to ""
    :return: Translated docstring
    :rtype: str

    """
    out = re.sub(r":param.*:", lambda x: _translate_parameter(x, fullname), s)
    return out


def _translate_parameter(match: re.Match, fullname: str = "") -> str:
    """
    Translate parameter info into other language.

    :param match re.Match: Object containing the expression match with parameter name and type
    :param str fullname: Full function name
    """
    s = match[0].strip(":").split()

    content = ' '.join([*[d_(typ) for typ in s[0:-1]], f_(fullname, s[-1])])
    t = ':' + content + ':'
    return t


def remove_injected_argument(s: str, remove_arg: str) -> str:
    """
    Remove any parameters for arguments that will be injected.
    """
    regexp = ":param.*" + remove_arg + r": (?s:.)*?\n(?=\n|(:param))"
    out = re.sub(regexp, "", s)
    return out


def remove_python_code_blocks(s: str) -> str:
    """
    Remove any markdown python code blocks.

    Fencing may be with triple backticks or colons.

    """
    # Replace python with nothing
    ret = re.sub(r"(:::|```)\s*(\{code\})?\s*python.*\n[\s\S]*?\n.*(:::|```)", "", s)
    return ret
