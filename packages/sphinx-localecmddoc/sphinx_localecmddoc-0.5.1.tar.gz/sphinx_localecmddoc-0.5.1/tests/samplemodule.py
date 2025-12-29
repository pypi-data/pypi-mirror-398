#!/usr/bin/env python3

from localecmd import Module, printout, programfunction


@programfunction()
def Func(a: int = 9, *b: float, cC: int = 8, **d: str):  # pragma: no cover
    """
    This is a docstring

    This has many lines

    ```python
    Doctest example
    >>> Func()

    ```
    ```{lcmd-example}
    Func 8 9 10 -cC 80
    ```

    """
    printout(a)


@programfunction()
def Func2(a: str = "9"):  # pragma: no cover
    """
    This is a docstring with some directive fence

    :param int a: A number

    ```{lcmd-example}
    Func2 "Hello world"
    ```
    """
    printout(a)


module = Module('test', [Func, Func2], 'Module docstring')

# Output to be parsed with myst-parser and sphinx
expected_output = """# Module test
Module docstring

````{py:function} Func a b... -cC -d... 

This is a docstring

This has many lines


```{lcmd-example}
Func 8 9 10 -cC 80
```
````
````{py:function} Func2 a 

This is a docstring with some directive fence

:param int a: A number

```{lcmd-example}
Func2 "Hello world"
```
````
"""

# output as result from sphinx with markdown builder
expected_output_built_md = """# Module test

Module docstring

### Func a b... -cC -d...

This is a docstring

This has many lines

```bash
¤ Func 8 9 10 -cC 80
8
```

### Func2 a

This is a docstring with some directive fence

* **Parameters:**
  **a** (*int*) – A number

```bash
¤ Func2 "Hello world"
Hello world
```


"""

# output as result from sphinx with markdown builder with lowered text
expected_output_built_md_lower = """# module test

module docstring

### func a b... -cc -d...

this is a docstring

this has many lines

```bash
¤ func 8 9 10 -cc 80
8
```

### func2 a

this is a docstring with some directive fence

* **parameters:**
  **a** (*int*) -- a number

```bash
¤ func2 "hello world"
hello world
```


"""

# output as result from sphinx with markdown builder
expected_output_package = """# Module package

Module docstring

### Func a b... -cC -d...

This is a docstring

This has many lines

```bash
¤ Func 8 9 10 -cC 80
8
```

### Func2 a

This is a docstring with some directive fence

* **Parameters:**
  **a** (*int*) – A number

```bash
¤ Func2 "Hello world"
Hello world
```

"""
