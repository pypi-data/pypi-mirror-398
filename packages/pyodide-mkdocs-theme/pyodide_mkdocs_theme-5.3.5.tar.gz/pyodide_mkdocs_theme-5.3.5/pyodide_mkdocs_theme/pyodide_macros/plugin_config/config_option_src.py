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

import sys

from pyodide_mkdocs_theme.pyodide_macros.tools_and_constants import Dumping

IS_PY_3_9 = (sys.version_info.major, sys.version_info.minor) == (3,9)

import re
from abc import ABCMeta
from typing import Any, Callable, ClassVar, List, Optional, TYPE_CHECKING, Tuple, Type, Union
from dataclasses import dataclass, fields
from functools import reduce

from mkdocs.config import config_options as C
from mkdocs.config.base import BaseConfigOption, ValidationError




from ..exceptions import PmtConfigurationError, PmtInternalError
from ..pyodide_logger import logger
from ..messages.fr_lang import LangFr
from ._string_tools_and_constants import PMT_PM_PREFIX_SIZE, DeprecationTemplate, get_python_type_as_code
from .common_tree_src import CommonTreeSrc, DeprecationStatus

if TYPE_CHECKING:
    from ..plugin.pyodide_macros_plugin import PyodideMacrosPlugin




DEFAULT_LANG = LangFr()






@dataclass
class ConfigOptionSrcDumpable(CommonTreeSrc, metaclass=ABCMeta):
    """
    Define a Config element, that can be dumped as mkdocs C.OptionItem for a plugin Config.
    Teh current/live value can then be extracted automatically from the PyodideMacrosPlugin
    object directly within the MkDocsConfig hierarchy.
    This hierarchy will be rotated on the fly to handle metadata configs (.pmt.meta.yml or
    md headers).
    """

    # ------------------------------------------------------------------------
    # kwargs only:


    conf_type: Optional[BaseConfigOption] = None
    """
    ConfigOption to use for this argument.
    If not given, use automatically `C.Type(py_type, default=self.default)`.
    """

    extended_validation: Optional[Callable[[Any], bool]] = None
    """
    optional predicate, that can be used to overcome the failure of the value validation against
    `self.conf_type.validate(...)`.
    """

    default: Optional[Any] = None
    """
    Default value for the conf_type. Ignored if None (use is_optional for this).
    """

    is_optional: bool = False
    """
    If True, add a C.Optional wrapper around the conf_type (given or generated).
    """

    index: Optional[int] = None
    """
    Index of the argument in the `*args` tuple, if it's positional.
    If index is -1, means the argument itself is a varargs.

    Can also be set automatically at instantiation time passing is_varargs=True instead.
    """

    is_varargs: bool = False
    """ Alternative way to define self.index (to use only at instantiation time) """


    def is_positional(self):
        """ Is a positional argument or a varargs? """
        return self.index is not None



    def __post_init__(self):
        super().__post_init__()

        if self.is_varargs and self.index is None:
            raise PmtConfigurationError(
                f"{self.name} argument is declared as varargs, but is missing it's positional index."
            )

        if self.is_in_config:

            if self.conf_type is None:
                # Reminder: "default=None" means "required" in mkdocs ConfigOptions.
                self.conf_type = C.Type(self.py_type, default=self.default)

            elif self.default is not None and self.default != self.conf_type.default:
                # NOTE: copy_with requires the second condition so that everything works correctly.
                raise PmtConfigurationError(
                    f"{self} as a `conf_type` argument, hence it shouldn't have a `default` one."
                )
            else:
                self.default = self.conf_type.default

            if self.is_optional:
                self.conf_type = C.Optional(self.conf_type)



    def copy_with(self, **kw):
        """
        Create a copy of the current instance, possibly changing some things on the fly.
        """
        args = {
            field.name: getattr(self, field.name)
                for field in fields(self.__class__)
                if field.name not in self.INTERNALS
        }
        args.update(kw)

        # If a default override is given, remove the conf_type entry
        # WARNING: this might break if the conf_type is not simple...
        if 'default' in kw:
            args['conf_type'] = None

        return self.__class__(**args)



    def to_config(self):
        return self.conf_type












@dataclass
class ConfigOptionSrcMaestroArticulated(ConfigOptionSrcDumpable, metaclass=ABCMeta):
    """
    Handle the articulation between data of ConfigOptionSrc and the PyodideMacroPlugin
    (setters, getters, observers).
    """

    fake_code_type: Optional[Type] = None
    """
    If defined, used instead of `self.py_type` when generating various codes in the project.
    (BaseMaestro getters, MacroData codes and docs).
    """

    # None hoping for failure if used at the wrong time...
    maestro_extractor_getter_name: str = None
    """
    MaestroBase property name (ConfigExtractor).
    WARNING: available only after build_accessor has been run!
    """

    value_transfer_processor: Optional[Callable[[Any],Any]] = None
    """
    If the option is not deprecated, this function must be wrapping the ConfigExtractor getter,
    to update the value on the fly (possibly pushing a warning in the logger).
    If the option is deprecated, the function may be used as conversion function, used when
    automatically transferring the value from a deprecated option to it's new location.
    """

    alternative: str = ""
    """
    Alternative getter to use if the current value is falsy (useful for lang messages, for example).
    """

    def __post_init__(self):
        if self.alternative.startswith('env.'):
            raise PmtConfigurationError(
                f"{ self.__class__.__name__ }(name='{self.name}', alternative={self.alternative!r}):\n"
                f"self.alternative should not start with 'env.'"
            )
        return super().__post_init__()


    def build_accessor(self, path: List[str]):
        """
        Register the internal properties `config_setter_path` and `maestro_extractor_getter_name`
        for the current instance, given the path of attributes to reach it from the root config
        object.
        """
        super().build_accessor(path, is_terminal=True)



    def get_default_or_live_env_default(self, env: Optional['PyodideMacrosPlugin']):
        """
        Extract the default value from the ConfigOptionSrc object. If it's None and it holds an
        `alternative` "getter", extract it from the live MacroPluginConfig object (or return None if it is not given.)
        """
        value = self.default
        if value is None and self.alternative and env:
           value = eval('env.'+self.alternative, {'env':env})
        return value


    def get_current_value(self, env:'PyodideMacrosPlugin', deprecated=False):
        """
        Get the current config value for this argument.

        @deprecated: when an option gets deprecated but the BaseMaestro getters are not yet
        up to date (dev apply or docs commands), the old name must be searched for. This
        argument allows this alternative property access.
        """
        prop = self.maestro_extractor_getter_name
        if deprecated and hasattr(env, prop[1:]):
            prop = prop[1:]

        value = getattr(env, prop)
        if self.is_varargs and value is None:
            return ()
        return value



    def set_value(self, value:Any, env:'PyodideMacrosPlugin', path:Optional[str]=None):
        """
        Set the current config value for this argument.
        """
        if path:
            *path, name = path.split('.')
        else:
            path, name = self.config_setter_path, self.name

        obj = reduce(getattr, path, env)
        obj[name] = value













@dataclass
class ConfigOptionSrcDeprecationHandler(ConfigOptionSrcMaestroArticulated, metaclass=ABCMeta):
    """
    Deprecation related logistics:

    - Actually deprecated config options.
    - NOT deprecated config options whose the value has to be extracted from another deprecated
      config option, IF it has been set.

    This is implemented for backward compatibility on breaking changes, allowing to define what
    to do on the way:
        1. Only raise warnings
        2. Raise errors
    And in both cases, this allows to give precise feedback to the user about what needs to be
    changed to update their mkdocs.yml file (or meta...) to avoid the warnings/errors.
    """


    moved_to: str = ""
    """
    For DeprecationStatus.moved only: where to transfer the value.
    """


    def __post_init__(self):
        super().__post_init__()

        if self.is_deprecated:
            if self.default is not None:
                raise PmtConfigurationError(
                    "Something suspicious happened: deprecated options shouldn't have default "
                    f"values: ({ self } with default={ self.default })"
                )
            if not isinstance(self.conf_type, C.Optional):      # deprecated is aAlways optional!
                self.conf_type = C.Optional(self.conf_type)

            self.conf_type = C.Deprecated(option_type=self.conf_type)




    def handle_deprecation_or_changes(self, env:'PyodideMacrosPlugin'):
        """
        If an argument/config option isn't deprecated but has a value_transfer_processor callback,
        replace the current value with the original one fed to the callback.

        If the argument.option is deprecated and the value is not None, handle any post processing
        (moving and/or modifying the current value on the fly), and warn the user (either with a
        simple warning, or an error, depending on the configuration).

        NOTE: the caller makes sure `ConfigExtractor.RAISE_DEPRECATION_ACCESS` is False, so that the
              value of the current argument/option can be extracted in the plugin instance.
        """
        if not self.is_deprecated and self.value_transfer_processor:
            value = self.get_current_value(env)
            fresh = self.value_transfer_processor(value)
            self.set_value(fresh, env)
            return

        if self.is_deprecated:
            value = self.get_current_value(env, deprecated=True)
            if value is None:
                return

            if self.deprecation_status == DeprecationStatus.moved:
                target = re.sub(r'^config', 'pyodide_macros', self.moved_to)
                logger.info(f"Reassign { self.py_macros_path } to { target }")

                if self.value_transfer_processor:
                    value = self.value_transfer_processor(value)

                self.set_value(value, env, path=self.moved_to)

            template: str = getattr(DeprecationTemplate, self.deprecation_status)
            full_msg = template.format(src=self.py_macros_path, moved_to=self.moved_to)
            return full_msg


    def yield_invalid_yaml_paths_or_values(self, value:Any, arg_only=False):
        """
        Check that the given property name, in the given meta_dct, is actually an option
        or a subconfig of the current instance, and yield an error message when an invalid
        property is found.
        """
        #Check or deprecation:
        yield from super().yield_invalid_yaml_paths_or_values(value)

        # Validate the current value
        if self.extended_validation and self.extended_validation(value):
            return

        try:
            self.conf_type.validate(value)
        except ValidationError as e:

            # Allow int vs bool values:
            if getattr(self.conf_type, '_type', None) is bool and type(value) is int:
                return

            path = self.name if arg_only else f"`{ self.py_macros_path[PMT_PM_PREFIX_SIZE:] }`"
            yield False, f"{ path } value is not valid. { e }"












@dataclass
class ConfigOptionSrcToDocs(ConfigOptionSrcDeprecationHandler, metaclass=ABCMeta):
    """
    Represent the docs related information about an argument of a macro.
    """

    # ------------------------------------------------------------------------
    # kwargs only:

    fake_name: Optional[str] = None
    """ If defined, override the argument name anywhere needed in the docs. """

    fake_type: Optional[str] = None
    """ If defined, override the argument type anywhere needed in the docs. """

    fake_default: Optional[str] = None
    """ If defined, override the default anywhere needed in the docs. """

    ide_link: bool=False
    """
    If True, when generating `as_table_row`, an md link will be added at the end, pointing
    toward the equivalent argument in the IDE-details page.
    """

    line_feed_link: bool = True
    """
    Add a line feed or not, before the ide_link when rendering `as_table_row`.
    """


    def __post_init__(self):
        super().__post_init__()


    def get_name_for_docs(self, allow_varargs=True):
        if self.fake_name is not None:
            return self.fake_name
        return '*' * allow_varargs * self.is_varargs + self.name


    def get_type_for_docs(self, use_default_if_not_None=False):
        """
        Return the string to use to describe de type of this argument in the docs.

        Used when:
        - building arguments tables (one argument only per table)
        - building functions' signature
        """
        if self.fake_type is not None:
            return self.fake_type
        actual_default = self.get_default_for_docs()
        if use_default_if_not_None and actual_default is not None:
            return repr(actual_default)
        return self.get_python_type_as_code()

    def get_python_type_as_code(self):
        return get_python_type_as_code(self.fake_code_type or self.py_type)

    def get_default_for_docs(self):
        if self.fake_default is not None:
            return self.fake_default
        return self.default


    @property
    def doc_name_type_min_length(self):
        """
        Compute the length of the `f"{name}:{type}"` string.
        """
        name_size = len(self.get_name_for_docs())
        return 1 + name_size + len(self.get_type_for_docs())


    def signature(self, size:int=None):
        """
        Build a prettier signature, with default values assignment vertically aligned, of the
        macro call signature.
        """
        length   = self.doc_name_type_min_length
        n_spaces = length if size is None else size - length + 1
        name     = self.get_name_for_docs()
        type_str = self.get_type_for_docs()
        default  = self.get_default_for_docs()
        return f"\n    { name }:{ ' '*n_spaces }{ type_str } = {default!r},"



    def as_table_row(self, only=True):
        """
        Generate a md table row for this specific argument.

        @only:  Conditions what is used for arg name, type and value.
                It is `False` when building IDE "per argument tables" (aka, with
                `macro_args_table(..., only=...)`.

                `only`  |  True     |  False
                --------|-----------|------------------------------------
                `col1`  |  type     |  nom argument
                `col2`  |  default  |  type (or default if it is not None)
                `col3`  |  docs     |  docs + ide_link if needed
        """

        if only:
            col1, col2, col3_doc, extras = (
                f"#!py { self.get_type_for_docs() }",
                repr(self.get_default_for_docs()),
                self.docs,
                '\n\n' + self.extra_docs,
            )
        else:
            col1, col2, col3_doc, extras = (
                self.get_name_for_docs(),
                self.get_type_for_docs(use_default_if_not_None=True),
                self.docs,
                ''
            )
            if self.ide_link:
                name      = self.get_name_for_docs(allow_varargs=False)
                col3_doc += "<br>" * self.line_feed_link
                col3_doc += f"_([plus d'informations](--IDE-{ name }))_"

        return f"| `{ col1 }` | `#!py { col2 }` | { col3_doc } |{ extras }"
















@dataclass
class ConfigOptionSrc(
    ConfigOptionSrcToDocs,
    ConfigOptionSrcDeprecationHandler,
    ConfigOptionSrcMaestroArticulated,
    ConfigOptionSrcDumpable,
):
    """
    Top level concrete class representing a "BaseConfigOption to be" (mixin!).
    """




@dataclass
class ConfigOptionIdeLink(ConfigOptionSrc):
    """ Reduce boiler plate for ConfigOptionSrc instances. """

    def __post_init__(self):
        self.ide_link = True
        super().__post_init__()




@dataclass
class ConfigOptionDeprecated(ConfigOptionSrc):
    """
    Reduce boiler plate for ConfigOptionSrc instances.
    By default, creates an "unsupported" deprecated object.
    """

    def __post_init__(self):
        self.deprecation_status = self.deprecation_status or DeprecationStatus.unsupported
        self.inclusion_profile  = Dumping.config_and_internals
        if self.moved_to:
            self.moved_to = f'config.{ self.moved_to }'
            self.deprecation_status = DeprecationStatus.moved

        super().__post_init__()




@dataclass
class ConfigOptionNumber(ConfigOptionSrc):
    """
    Reduce boiler plate for ConfigOptionSrc instances, using a generic logistic to define  float|int.
    """
    def __post_init__(self):

        self.py_type = (float if IS_PY_3_9 else Union[float,int])
        if not self.is_optional:
            self.default = 0.0
        self.fake_type = "float|int"
        self.fake_code_type = Union[float, int]
        self.extended_validation = ((lambda v: isinstance(v, (int,float))) if IS_PY_3_9 else None)
        self.yaml_schema_dct={"type": 'number'}
        self.docs += """

{{orange("ATTENTION :")}} Si vous utilisez Python 3.9, la valeur pour cette option
depuis le fichier `mkdocs.yml` ne peut être qu'un `#!py float`. Si elle est utilisée
depuis d'autres endroits (argument de macro, fichiers {{ meta() }}, entêtes markdown),
cela peut aussi être un `#!py int`."""

        super().__post_init__()
