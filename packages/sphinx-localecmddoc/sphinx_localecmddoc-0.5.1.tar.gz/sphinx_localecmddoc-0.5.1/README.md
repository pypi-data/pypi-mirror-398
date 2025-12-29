# sphinx-localecmddoc

Sphinx extension for autodocumenting [localecmd](https://codeberg.org/jbox/localecmd) modules
The extension is hard-coded to generate markdown to be parsed with the myst-parser.

## Install
The commands assume that your virtual environment is activated in the terminal.
The installation will also install the needed dependencies if not present:

- Sphinx
- Myst-parser
- Localecmd (which is needed for what to document)

### Install from pypi
To install the package and its dependencies, run
```
pip install sphinx-localecmddoc
```
Remember to add the dependency to the pyproject.toml (or equvalent)
### Install from git (not recommended, but only option)
To install the package and its dependencies, run
```
pip install sphinx-localecmddoc @ git+https://codeberg.org/jbox/sphinx-localecmddoc.git@main
```

## Quickstart
The following assumes that you already have set up sphinx with myst-parser.

Within the `conf.py`, add the extension to the extension list:
```python
extensions = [
...
    'localecmddoc',
...
]
```

Localecmddoc does not search for localecmd.Modules.
Instead they must be given explicitly to the configuration.
A basic start is simply using the module with functions provided by localecmd.

```python
localecmd_modules = {
    'localecmd.builtins': 'localecmd-builtins',
    }
```

Add its index file to a toctree (example in restructured text)
```
.. toctree
   ...
   functions/index.md
   ... (other files)
```

When running sphinx, a folder `functions` will be created containing the documentation of every module.
The file `localecmd-builtins.md` will contain the documentation of the `localecmd.builtins` module.


## Contribute
Thank you for contributing!

The [contributing section of the documentation](https://jbox.codeberg.page/sphinx-localecmddoc/contribution)
 will help you to the start.

