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


from abc import ABCMeta
from dataclasses import dataclass
from itertools import takewhile
from typing import ClassVar, Tuple, Type, Union

from mkdocs.config import config_options as C, Config



from ..plugin_tools.maestro_tools import CopyableConfig
from ._string_tools_and_constants import PMT_PM_PREFIX_SIZE
from .common_tree_src import CommonTreeSrc
from .config_option_src import ConfigOptionSrc








@dataclass
class SubConfigSrc(CommonTreeSrc):
    """
    Class making the link between:
        - The actual python implementation
        - The docs content (avoiding out of synch docs)
        - The Config used for the .meta.pmt.yml features. Note that optional stuff "there" is
          different from an optionality (or it's absence) in the running macro/python layer.

    Those instances represent the config "starting point", so all defaults are applied here,
    for the Config implementation.
    When extracting meta files or meta headers, the CopyableConfig instances will receive dicts
    from the yaml content, and those will be merged in the current config. This means the dict
    itself can contain only partial configs, it's not a problem.
    The corollary of this, is that _only_ values that could be None at runtime as an actual/useful
    value should be declared as `C.Optional`.
    """

    is_config: bool = True
    """ Override parent value. """

    is_varargs: bool = False
    """ Override parent value. """

    BASES: ClassVar[Tuple[Type]] = (CopyableConfig,)
    """ Extensions for the MkDocs Config object to create from the current instance. """

    def __post_init__(self):
        super().__post_init__()
        self.subs_dct = {arg.name: arg for arg in self.elements}

        if len(self.subs_dct) != len(self.elements):
            raise ValueError(
                f"{ self }: duplicated name for sub config elements." + ''.join(
                    f"\n    {elt}" for elt in self.elements
                )
            )

        if self.long_accessor:
            for elt in self.elements:
                elt.long_accessor = True


    def get_mro(self):
        chain = ", ".join( kls.__name__ for kls in self.BASES + (Config,))
        return f"({ chain })"


    def __getattr__(self, prop):
        if not self.has(prop):
            raise AttributeError(f"{ self }: no { prop } attribute")
        return self.subs_dct[prop]


    def build_mkdocs_config_class_body(self):
        body = {
            name: child.to_config()
                for name,child in self.subs_dct.items()
                if child.is_in_config
        }
        body['__docs__'] = self.extra_docs
        return body


    def to_config(self):
        """
        Dynamically and recursively convert to the equivalent CopyableConfig objects hierarchy.
        All intermediate classes are dynamically creates and instantiated on the fly.
        """
        class_name = self.build_dynamic_config_class_name()
        body = self.build_mkdocs_config_class_body()
        kls  = type(class_name, self.BASES, body)
        return C.SubConfig(kls)


    def yield_invalid_yaml_paths_or_values(self, meta_dct:dict):
        """
        Check that the given property name, in the given meta_dct, is actually an option
        or a sub-config of the current instance, and yield an error message when an invalid
        property is found.
        """
        #Check or deprecation:
        yield from super().yield_invalid_yaml_paths_or_values()

        # Validate the sub-config elements:
        for prop,value in meta_dct.items():
            path = f"{ self.py_macros_path[PMT_PM_PREFIX_SIZE:] }.{ prop }".lstrip('.')
            if not self.has(prop):
                yield False, f"`{ path }` is not a valid configuration option for pyodide_macros."
            else:
                sub = self.subs_dct[prop]
                yield from sub.yield_invalid_yaml_paths_or_values(value)








ConfOrOptSrc = Union[ConfigOptionSrc, SubConfigSrc]
"""
Union type: regroup instances of ConfigOptionSrc and SubConfigSrc (basically,
revolves around the behaviors of CommonTreeSrc).
"""
