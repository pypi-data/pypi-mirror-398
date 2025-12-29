"""
pyodide-mkdocs-theme
Copyleft GNU GPLv3 🄯 2024 Frédéric Zinelli

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.
If not, see <https://www.gnu.org/licenses/>.
"""


import re
from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Optional, TYPE_CHECKING

from mkdocs.config.base import Config


from ..parsing import camel

if TYPE_CHECKING:
    from ..plugin.pyodide_macros_plugin import PyodideMacrosPlugin










class CopyableConfig(Config):
    """
    CopyableConfig instances can copy themselves, merging them with a given dict-like object
    (potentially another mkdocs Config object) and return a brand new object.
    """

    def copy(self):
        """ Recursively create a copy of self """
        other = self.__class__()
        for k,v in self.items():
            other[k] = v.copy() if isinstance(v, CopyableConfig) else v
        return other


    def copy_with(self, yml_nested_dct:dict, consume_dict=False):
        """
        Create a copy of the current config object, updating on the fly the values with the
        content of the given dict.
        If no keys are matching any of the current object, just return the current object,
        to speed up the process.

        Reasonning:
        - The config objects are never mutated.
        - The fields that are not in the dict argument won't be mutated, so the current config
          can be used.
        - When a field is in the dict, the current object has to be replaced with a fresh one.
        """
        if not any(filter(self.__contains__, yml_nested_dct.keys())):
            return self

        fresh = self.__class__()
        for k,v in self.items():
            if k not in yml_nested_dct:
                fresh[k] = v
                continue

            val = yml_nested_dct.pop(k) if consume_dict else yml_nested_dct[k]
            if not isinstance(v, CopyableConfig):
                fresh[k] = val
            else:
                fresh[k] = v.copy_with(val, consume_dict)
        return fresh











@dataclass
class ConfigExtractor:
    """
    Data descriptor extracting automatically the matching property name from the mkdocs config.
    An additional path (dot separated keys/properties) can be provided, that will be prepended
    to the property name.
    """


    RAISE_DEPRECATION_ACCESS: ClassVar[bool] = False
    """
    Accessing the value on getters marked as deprecated will raise an error if this flag is True.
    This is defensive programming, to make sure PMT code isn't using those anymore.

    Note: False at the beginning because during on_config, the theme will check if the user set
          some values for deprecated options, so the access should work the first time.
          See `PluginConfigSrc.spot_usage_of_deprecated_features(env)` for more information.
    """

    #----------------------------------------------------------------------------------------

    path: str = ''
    """
    Dots separated path to the OptionConfigSrc element (without its name).
    """

    prop: Optional[str] = None
    """
    Name of the ConfigOptionSrc element. If None, defined automatically through __set_name__.
    """

    alternative: Optional[str] = None
    """
    If the extracted value is None, try to access this value instead, as `env.config.(...)`.
    """

    deprecated: bool = False
    """
    If True, accessing this property will call `env.warn_unmaintained` method, once the
    cls.RAISE_DEPRECATION_ACCESS value has become True.
    """

    transform: Optional[str] = None
    """
    Transform the value extracted from the config on the fly before returning it, if defined.
    """

    _getter: Optional[Callable[['PyodideMacrosPlugin'],Any]] = None
    """
    Internal getter to get fast access to the values (in the form `lambda env: env.config.(...)`).
    """


    def __set_name__(self, _kls, over_prop:str):
        path = self.path
        if not self.prop:
            self.prop = over_prop if not self.deprecated else over_prop.lstrip('_')

        # Using an evaluated function gives perfs equivalent to the previous version using a
        # cache, while keeping everything fully dynamic (=> needed for meta.pmt.yml tools)
        env_prop = 'env.' + '.'.join((path, self.prop)).strip('.').replace('..','.')

        if not re.fullmatch(r'\w([\w.]*\w)?', env_prop):
            raise ValueError(
                f"Invalid code. cannot build ConfigExtractor({self.path}, prop={self.prop!r}) "
                 "alternative getter."
            )

        if self.alternative:
            if not re.fullmatch(r'\w([\w.]*\w)?', self.alternative):
                raise ValueError(
                    f"Invalid code. cannot build ConfigExtractor({self.path}, prop={self.prop!r}) "
                    f"alternative getter with: {self.alternative!r}"
                )
            env_prop = f"v if (v:={ env_prop }) is not None else env.{ self.alternative }"

        self._getter = value_getter = eval(f"lambda env: { env_prop }")   # pylint: disable=eval-used
        if self.transform:
            self._getter = lambda env: self.transform(value_getter(env))


    def __get__(self, env:'PyodideMacrosPlugin', kls=None):
        if self.deprecated and self.RAISE_DEPRECATION_ACCESS:
            env.warn_unmaintained(f'The option {self.prop}')
        out = self._getter(env)
        return out


    def __set__(self, *a, **kw):
        raise ValueError(f"The {self.prop} property should never be reassigned")











class AutoCounter:
    """
    Counter with automatic increment. The internal value can be updated/rested by assignment.
    @warn: if True, the user will see a notification in the console about that counter being
    unmaintained so far (displayed once only).

    WARNING: this is a class level-based counter.
    """

    def __init__(self, warn=False):
        self.cnt = 0
        self.warn_once = warn

    def __set_name__(self, _, prop:str):
        self.prop = prop        # pylint: disable=attribute-defined-outside-init

    def __set__(self, _:'PyodideMacrosPlugin', value:int):
        self.cnt = value

    def __get__(self, obj:'PyodideMacrosPlugin', _=None):
        if self.warn_once:
            self.warn_once = False
            obj.warn_unmaintained(f'The property {self.prop!r}')
        self.cnt += 1
        return self.cnt

    def inc(self):
        """ when not used as descriptor... """
        self.cnt += 1
        return self.cnt










def dump_as_dct_with_camel_case(props, obj:Optional[Any]=None, converter:Optional[Callable]=None):
    """
    Convert the given properties of an object to a dict where:
    * Keys are camelCased property names
    * If @obj is `None`, use `None` as values.
    * Otherwise, the values are converted through the `converter` function.
    """
    return {
        camel(prop): converter( getattr(obj, prop) if obj else None )
        for prop in props
    }
