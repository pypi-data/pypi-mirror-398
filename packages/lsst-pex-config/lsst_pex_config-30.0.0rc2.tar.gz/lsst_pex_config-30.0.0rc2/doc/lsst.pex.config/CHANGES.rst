lsst-pex-config v29.0.0 (2025-03-25)
====================================

New Features
------------

- Introduced the ``keyCheck`` callback to ``DictField`` and ``ConfigDictField``, allowing custom key validation during assignment. Added unit tests to ensure functionality. (`DM-48074 <https://rubinobs.atlassian.net/browse/DM-48074>`_)
- Make the messages emitted by ``compareConfigs`` consistently start with the fully-qualified name of the config field. (`DM-49121 <https://rubinobs.atlassian.net/browse/DM-49121>`_)


lsst-pex-config v28.0.0 (2024-11-21)
====================================

No significant changes.


lsst-pex-config v27.0.0 (2024-05-29)
====================================

- Improved all docstrings to make them compliant with Numpydoc.
- Minor code cleanups driven by Ruff linting. (`DM-42116 <https://rubinobs.atlassian.net/browse/DM-42116>`_)

lsst-pex-config v26.0.0 (2023-09-22)
====================================

New Features
------------

- Added a dynamic-default callback argument to ``RegistryField``. (`DM-31924 <https://rubinobs.atlassian.net/browse/DM-31924>`_)
- Introduced ``ConfigurableActions``. These are ``pex_config`` fields and config types which function as a functor, state is set at config time, but the ``ConfigurableActions`` are callable at runtime to produce an action. (`DM-36649 <https://rubinobs.atlassian.net/browse/DM-36649>`_)


API Changes
-----------

- The ``loadFromStream`` and ``loadFromString`` methods now take a dictionary as an optional argument which allows specifying additional variables to use in local scope when reading configs. (`DM-40198 <https://rubinobs.atlassian.net/browse/DM-40198>`_)


Other Changes and Additions
---------------------------

- There is now a requirement for configuration parameters to have a non-empty docstring. (`DM-4037 <https://rubinobs.atlassian.net/browse/DM-4037>`_)


lsst-pex-config v25.0.0 (2023-02-28)
====================================

Other Changes and Additions
---------------------------

- Some sorting now happens when saving config files (via DM-33027). (`DM-35060 <https://rubinobs.atlassian.net/browse/DM-35060>`_)


lsst-pex-config v24.0.0 (2022-08-30)
====================================

New Features
------------

* Add support for python typing of Fields. (DM-35312)
* ``loadFromStream`` now accepts a file-like object. (DM-32733)

Removals
--------

* The old ``root`` name in configuration files has been removed. (DM-32759)
* The Python2 iteration methods (``iterkeys``, etc) have been removed (DM-7148)

Other Changes
-------------

* Attempting to pickle a proxy object now fails with a useful error message. (DM-33963)

lsst-pex-config v23.0.0 (2021-12-21)
====================================

Other Changes
-------------

* Internal data structures have been modified to aid Python reference counting. (DM-31507)

lsst-pex-config v22.0.0 (2021-07-09)
====================================

Other Changes
-------------

* Fix some issues with history handling. (DM-27519)

lsst-pex-config v21.0.0 (2020-12-08)
====================================

New Features
------------

* Configuration objects can now be serialized to YAML. (DM-26008)

lsst-pex-config v20.0.0 (2020-06-24)
====================================

New Features
------------

* ``__file__`` can now be accessed within a config file.
  This allow the config to acccess another config file relative to this one without having to use an environment variable or ``getPackageDir``. (DM-23359)

Bug Fixes
---------

* Freezing a config no longer affects other instances of that config. (DM-24435)

Other Changes
-------------

* It is now possible to print a configuration without the associated imports. (DM-22301)

lsst-pex-config v19.0.0 (2019-12-05)
====================================

New Features
------------

* Now released under a dual GPLv3 and 3-clause BSD license.
* Add support for deprecating configuration fields. Such fields are not written out. (DM-20378)
* ``pex_policy`` and ``daf_base`` are now optional dependencies, and the dependency on the LSST ``utils`` package in testing has been removed. (DM-21064)
