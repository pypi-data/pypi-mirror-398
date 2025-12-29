#!/usr/bin/env python3
""" """

import inspect

from localecmd import Function

from localecmddoc.autodoc import (
    create_module_doc_output,
    getdoc_cmd,
    remove_injected_argument,
    remove_python_code_blocks,
)
from tests.samplemodule import expected_output, module


def test_module_output():
    output = create_module_doc_output(module, remove_pycode=True)
    assert output.strip() == expected_output.strip()


def test_pycode_block_removal():
    doc = inspect.cleandoc("""
    :::{code} python
    >>> func2(1, 2, 3, 4)

    >>> func2(1, b=4)
    :::
    """)
    tdoc = remove_python_code_blocks(doc)
    assert tdoc == inspect.cleandoc("")

    doc2 = inspect.cleandoc("""
    :::{code} python
    >>> func2(1, 2, 3, 4)

    >>> func2(1, b=4)
    :::
        
    ```python
    >>> func2(1, 2, 3, 4)

    >>> func2(1, b=4)
    ```
    ```bash
    ls
    ```
    """)
    tdoc2 = remove_python_code_blocks(doc2)
    assert tdoc2.strip() == inspect.cleandoc("""```bash\nls\n```""").strip()


def test_remove_injected_argument():
    title = "bla blo"
    atxt = ":param int a: keep"
    btxt = ":param int b: remove\nlong line"
    ctxt = ":param str c: keep\nlong line"
    dtxt = ":param str | int d: remove\nlong line"
    body = "Body"

    doc = '\n'.join([title, '\n', atxt, btxt, ctxt, dtxt, '\n', body])
    res = remove_injected_argument(doc, 'b')
    assert res == '\n'.join([title, '\n', atxt, ctxt, dtxt, '\n', body])
    res2 = remove_injected_argument(res, 'd')
    assert res2 == '\n'.join([title, '\n', atxt, ctxt, '\n', body])


def test_getdoc_cmd():
    header = "```py:function func a b c d \n"
    title = "bla blo"
    atxt = ":param int a: keep"
    btxt = ":param int b: remove\nlong line"
    ctxt = ":param str c: keep\nlong line"
    dtxt = ":param str | int d: remove\nlong line"
    body = "Body"
    footer = "```\n"

    doc = '\n'.join([title, '\n', atxt, btxt, ctxt, dtxt, '\n', body])

    def func(a, b, c, d):
        return 'a'

    func.__doc__ = doc
    cmd = Function(func)
    cmd.set_argument_substitutions(7, d=90)

    res = getdoc_cmd(cmd, 'py:function', remove_pycode=False)
    assert res == '\n'.join([header, title, '\n', btxt, ctxt, '\n', body, footer])
