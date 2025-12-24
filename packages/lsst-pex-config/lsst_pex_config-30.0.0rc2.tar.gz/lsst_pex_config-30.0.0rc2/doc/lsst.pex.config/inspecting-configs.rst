.. py:currentmodule:: lsst.pex.config

#########################
Inspecting configurations
#########################

Field access
------------

Iterating through a `Config` instance yields the names of the `Field` attributes it contains.
The `Config` class also supports many dictionary-like methods: `~Config.keys`, `~Config.items`, and `~Config.values`.

History
-------

The `Config.history` attribute contains the history of all changes to the `Config` instance's fields.
Each `Field` instance also has a history.
The `Config.formatHistory` method displays the history of a given `Field` in a more readable format.

Docstrings
----------

Each `Field` instance is required to have a ``doc`` attribute that describes the contents of the field.
These ``doc`` strings should be complete sentences and should give users of the `Config` object a good understanding of what the field is and how it will be interpreted and used.
Multi-sentence ``doc`` strings should have an explicit newline character (``"\n"``) after each sentence;
single newlines here do not affect the rendered HTML docs, but they improve the readability of the persisted `Config` object (as produced by `Config.save`).
`Field` ``doc`` strings are treated as reStructuredText when rendered, but we do not recommend using anything more than very simple formatting in them, to balance the formatting of the rendered HTML and the persisted `Config` (which just passes through the ``doc`` string as-is).

A class docstring can also be provided for the `Config` class as a whole, although this may be redundant with the class name.

You can use the built-in `help` function or :command:`pydoc` command to inspect a `Config` instance's doc strings as well as those of its `Field` attributes.
