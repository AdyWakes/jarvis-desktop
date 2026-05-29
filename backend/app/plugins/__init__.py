"""Drop-in plugin directory.

Any `.py` file in this directory that defines a `Tool` subclass (or exposes a
top-level `TOOLS` iterable of `Tool` instances) is auto-registered at startup.

See `example_plugin.py.example` for a template.
"""
