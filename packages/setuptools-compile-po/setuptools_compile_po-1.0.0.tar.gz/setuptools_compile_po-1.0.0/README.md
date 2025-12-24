# Setuptools compile po

Compile .po files to .mo files.

## Usage

Set in ``pyproject.toml``:

```toml
[build-system]
requires = ["setuptools", "setuptools-compile-po"]
...
```

This configuration compiles all ``.po`` files in the ``$package/locale`` folder.
Another path to the files is defined by the configuration:

```toml
[tool.setuptools_compile_po]
directory = "package/path/locale"
```

## Dependencies

The ``msgfmt`` command is used for compilation. It must be installed in the os.
For example, with the command ``apt install gettext``.
If you need to compile with a different command, you can define it with the ``msgfmt`` parameter:

```toml
[tool.setuptools_compile_po]
msgfmt = "command"
```
