# This file is part of pex_config.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This software is dual licensed under the GNU General Public License and also
# under a 3-clause BSD license. Recipients may choose which of these licenses
# to use; please see the files gpl-3.0.txt and/or bsd_license.txt,
# respectively.  If you choose the GPL option then the following text applies
# (but note that there is still no warranty even if you opt for BSD instead):
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ("Registry", "RegistryField", "makeRegistry", "registerConfig", "registerConfigurable")

import collections.abc
import copy

from .config import Config, FieldValidationError, _typeStr
from .configChoiceField import ConfigChoiceField, ConfigInstanceDict


class ConfigurableWrapper:
    """A wrapper for configurables.

    Used for configurables that don't contain a ``ConfigClass`` attribute,
    or contain one that is being overridden.

    Parameters
    ----------
    target : configurable class
        Target class.
    ConfigClass : `type`
        Config class.
    """

    def __init__(self, target, ConfigClass):
        self.ConfigClass = ConfigClass
        self._target = target

    def __call__(self, *args, **kwargs):
        return self._target(*args, **kwargs)


class Registry(collections.abc.Mapping):
    """A base class for global registries, which map names to configurables.

    A registry acts like a read-only dictionary with an additional `register`
    method to add targets. Targets in the registry are configurables (see
    *Notes*).

    Parameters
    ----------
    configBaseType : `lsst.pex.config.Config`-type
        The base class for config classes in the registry.

    Notes
    -----
    A configurable is a callable with call signature ``(config, *args)``
    Configurables typically create an algorithm or are themselves the
    algorithm. Often configurables are `lsst.pipe.base.Task` subclasses, but
    this is not required.

    A ``Registry`` has these requirements:

    - All configurables added to a particular registry have the same call
      signature.
    - All configurables in a registry typically share something important
      in common. For example, all configurables in ``psfMatchingRegistry``
      return a PSF matching class that has a ``psfMatch`` method with a
      particular call signature.

    Examples
    --------
    This examples creates a configurable class ``Foo`` and adds it to a
    registry. First, creating the configurable:

    >>> from lsst.pex.config import Registry, Config
    >>> class FooConfig(Config):
    ...     val = Field(dtype=int, default=3, doc="parameter for Foo")
    >>> class Foo:
    ...     ConfigClass = FooConfig
    ...
    ...     def __init__(self, config):
    ...         self.config = config
    ...
    ...     def addVal(self, num):
    ...         return self.config.val + num

    Next, create a ``Registry`` instance called ``registry`` and register the
    ``Foo`` configurable under the ``"foo"`` key:

    >>> registry = Registry()
    >>> registry.register("foo", Foo)
    >>> print(list(registry.keys()))
    ["foo"]

    Now ``Foo`` is conveniently accessible from the registry itself.

    Finally, use the registry to get the configurable class and create an
    instance of it:

    >>> FooConfigurable = registry["foo"]
    >>> foo = FooConfigurable(FooConfigurable.ConfigClass())
    >>> foo.addVal(5)
    8
    """

    def __init__(self, configBaseType=Config):
        if not issubclass(configBaseType, Config):
            raise TypeError(f"configBaseType={_typeStr(configBaseType)} must be a subclass of Config")
        self._configBaseType = configBaseType
        self._dict = {}

    def register(self, name, target, ConfigClass=None):
        """Add a new configurable target to the registry.

        Parameters
        ----------
        name : `str`
            Name that the ``target`` is registered under. The target can
            be accessed later with `dict`-like patterns using ``name`` as
            the key.
        target : obj
            A configurable type, usually a subclass of `lsst.pipe.base.Task`.
        ConfigClass : `lsst.pex.config.Config`-type, optional
            A subclass of `lsst.pex.config.Config` used to configure the
            configurable. If `None` then the configurable's ``ConfigClass``
            attribute is used.

        Raises
        ------
        RuntimeError
            Raised if an item with ``name`` is already in the registry.
        AttributeError
            Raised if ``ConfigClass`` is `None` and ``target`` does not have
            a ``ConfigClass`` attribute.

        Notes
        -----
        If ``ConfigClass`` is provided then the ``target`` configurable is
        wrapped in a new object that forwards function calls to it. Otherwise
        the original ``target`` is stored.
        """
        if name in self._dict:
            raise RuntimeError(f"An item with name {name!r} already exists")
        if ConfigClass is None:
            wrapper = target
        else:
            wrapper = ConfigurableWrapper(target, ConfigClass)
        if not issubclass(wrapper.ConfigClass, self._configBaseType):
            raise TypeError(
                f"ConfigClass={_typeStr(wrapper.ConfigClass)} is not a subclass of "
                f"{_typeStr(self._configBaseType)!r}"
            )
        self._dict[name] = wrapper

    def __getitem__(self, key):
        return self._dict[key]

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)

    def __contains__(self, key):
        return key in self._dict

    def makeField(self, doc, default=None, optional=False, multi=False, on_none=None):
        """Create a `RegistryField` configuration field from this registry.

        Parameters
        ----------
        doc : `str`
            A description of the field.
        default : object, optional
            The default target for the field.
        optional : `bool`, optional
            When `False`, `lsst.pex.config.Config.validate` fails if the
            field's value is `None`.
        multi : `bool`, optional
            A flag to allow multiple selections in the `RegistryField` if
            `True`.
        on_none : `Callable`, optional
            A callable that should be invoked when ``apply`` is called but the
            selected name or names is `None`.  Will be passed the field
            attribute proxy (`RegistryInstanceDict`) and then all positional
            and keyword arguments passed to ``apply``.

        Returns
        -------
        field : `lsst.pex.config.RegistryField`
            `~lsst.pex.config.RegistryField` Configuration field.
        """
        return RegistryField(doc, self, default, optional, multi, on_none=on_none)


class RegistryAdaptor(collections.abc.Mapping):
    """Private class that makes a `Registry` behave like the thing a
    `~lsst.pex.config.ConfigChoiceField` expects.

    Parameters
    ----------
    registry : `Registry`
        `Registry` instance.
    """

    def __init__(self, registry):
        self.registry = registry

    def __getitem__(self, k):
        return self.registry[k].ConfigClass

    def __iter__(self):
        return iter(self.registry)

    def __len__(self):
        return len(self.registry)

    def __contains__(self, k):
        return k in self.registry


class RegistryInstanceDict(ConfigInstanceDict):
    """Dictionary of instantiated configs, used to populate a `RegistryField`.

    Parameters
    ----------
    config : `lsst.pex.config.Config`
        Configuration instance.
    field : `RegistryField`
        Configuration field.
    """

    def __init__(self, config, field):
        ConfigInstanceDict.__init__(self, config, field)
        self.registry = field.registry

    def _getTarget(self):
        if self._field.multi:
            raise FieldValidationError(
                self._field, self._config, "Multi-selection field has no attribute 'target'"
            )
        return self.types.registry[self._selection]

    target = property(_getTarget)

    def _getTargets(self):
        if not self._field.multi:
            raise FieldValidationError(
                self._field, self._config, "Single-selection field has no attribute 'targets'"
            )
        return [self.types.registry[c] for c in self._selection]

    targets = property(_getTargets)

    def apply(self, *args, **kwargs):
        """Call the active target(s) with the active config as a keyword arg.

        Parameters
        ----------
        *args, **kwargs : `~typing.Any
            Additional arguments will be passed on to the configurable
            target(s).

        Returns
        -------
        result
            If this is a single-selection field, the return value from calling
            the target. If this is a multi-selection field, a list thereof.
        """
        if self.active is None:
            if self._field._on_none is not None:
                return self._field._on_none(self, *args, **kwargs)
            msg = "No selection has been made.  Options: {}".format(" ".join(self.types.registry.keys()))
            raise FieldValidationError(self._field, self._config, msg)
        return self.apply_with(self._selection, *args, **kwargs)

    def apply_with(self, selection, *args, **kwargs):
        """Call named target(s) with the corresponding config as a keyword
        arg.

        Parameters
        ----------
        selection : `str` or `~collections.abc.Iterable` [ `str` ]
            Name or names of targets, depending on whether ``multi=True``.
        *args, **kwargs
            Additional arguments will be passed on to the configurable
            target(s).

        Returns
        -------
        result
            If this is a single-selection field, the return value from calling
            the target. If this is a multi-selection field, a list thereof.

        Notes
        -----
        This method ignores the current selection in the ``name`` or ``names``
        attribute, which is usually not what you want.  This method is most
        useful in ``on_none`` callbacks provided at field construction, which
        allow a context-dependent default to be used when no selection is
        configured.
        """
        if self._field.multi:
            retvals = []
            for c in selection:
                retvals.append(self.types.registry[c](*args, config=self[c], **kwargs))
            return retvals
        else:
            return self.types.registry[selection](*args, config=self[selection], **kwargs)

    def __setattr__(self, attr, value):
        if attr == "registry":
            object.__setattr__(self, attr, value)
        else:
            ConfigInstanceDict.__setattr__(self, attr, value)


class RegistryField(ConfigChoiceField):
    """A configuration field whose options are defined in a `Registry`.

    Parameters
    ----------
    doc : `str`
        A description of the field.
    registry : `Registry`
        The registry that contains this field.
    default : `str`, optional
        The default target key.
    optional : `bool`, optional
        When `False`, `lsst.pex.config.Config.validate` fails if the field's
        value is `None`.
    multi : `bool`, optional
        If `True`, the field allows multiple selections. The default is
        `False`.
    on_none : `Callable`, optional
        A callable that should be invoked when ``apply`` is called but the
        selected name or names is `None`.  Will be passed the field attribute
        proxy (`RegistryInstanceDict`) and then all positional and keyword
        arguments passed to ``apply``.

    See Also
    --------
    ChoiceField
    ConfigChoiceField
    ConfigDictField
    ConfigField
    ConfigurableField
    DictField
    Field
    ListField
    RangeField
    """

    instanceDictClass = RegistryInstanceDict
    """Class used to hold configurable instances in the field.
    """

    def __init__(self, doc, registry, default=None, optional=False, multi=False, on_none=None):
        types = RegistryAdaptor(registry)
        self.registry = registry
        self._on_none = on_none
        ConfigChoiceField.__init__(self, doc, types, default, optional, multi)

    def __deepcopy__(self, memo):
        """Customize deep-copying, want a reference to the original registry.

        WARNING: this must be overridden by subclasses if they change the
        constructor signature!
        """
        other = type(self)(
            doc=self.doc,
            registry=self.registry,
            default=copy.deepcopy(self.default),
            optional=self.optional,
            multi=self.multi,
            on_none=self._on_none,
        )
        other.source = self.source
        return other


def makeRegistry(doc, configBaseType=Config):
    """Create a `Registry`.

    Parameters
    ----------
    doc : `str`
        Docstring for the created `Registry` (this is set as the ``__doc__``
        attribute of the `Registry` instance.
    configBaseType : `lsst.pex.config.Config`-type
        Base type of config classes in the `Registry`.

    Returns
    -------
    registry : `Registry`
        Registry with ``__doc__`` and ``_configBaseType`` attributes
        set.
    """
    cls = type("Registry", (Registry,), {"__doc__": doc})
    return cls(configBaseType=configBaseType)


def registerConfigurable(name, registry, ConfigClass=None):
    """Add a class as a configurable in a `Registry` instance.

    Parameters
    ----------
    name : `str`
        Name of the target (the decorated class) in the ``registry``.
    registry : `Registry`
        The `Registry` instance that the decorated class is added to.
    ConfigClass : `lsst.pex.config.Config`-type, optional
        Config class associated with the configurable. If `None`, the class's
        ``ConfigClass`` attribute is used instead.

    See Also
    --------
    registerConfig

    Notes
    -----
    Internally, this decorator runs `Registry.register`.
    """

    def decorate(cls):
        registry.register(name, target=cls, ConfigClass=ConfigClass)
        return cls

    return decorate


def registerConfig(name, registry, target):
    """Add a class as a ``ConfigClass`` in a `Registry` and
    associate it with the given configurable.

    Parameters
    ----------
    name : `str`
        Name of the ``target`` in the ``registry``.
    registry : `Registry`
        The registry containing the ``target``.
    target : obj
        A configurable type, such as a subclass of `lsst.pipe.base.Task`.

    See Also
    --------
    registerConfigurable

    Notes
    -----
    Internally, this decorator runs `Registry.register`.
    """

    def decorate(cls):
        registry.register(name, target=target, ConfigClass=cls)
        return cls

    return decorate
