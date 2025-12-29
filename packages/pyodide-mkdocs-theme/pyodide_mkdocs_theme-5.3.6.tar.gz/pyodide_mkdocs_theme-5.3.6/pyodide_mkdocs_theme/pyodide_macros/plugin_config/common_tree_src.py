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
from pathlib import Path
import re
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field



from ..exceptions import PmtConfigurationError
from ..tools_and_constants import Dumping
from ._string_tools_and_constants import PMT_PM_PREFIX_SIZE, DeprecationStatus, inline_md


if TYPE_CHECKING:
    from .sub_config_src import ConfOrOptSrc






@dataclass
class CommonTreeSrcBase:
    """
    Properties and/or methods that are common to ConfigOptionSrc and SubConfigSrc classes.

    Note: This is more of a reminder than anything, considering the properties, but it allows
          to enforce the interface when it comes to methods.
    """

    name: str = ''
    """ Element's name in the tree hierarchy. """

    py_type: Any = None
    """
    Type of the actual value, used at runtime in python (see BaseMaestro extractors / might
    not be aligned with the conf_type value for options).
    """

    elements: Tuple['ConfOrOptSrc'] = ()
    """ Sub elements of the current SubConfigSrc (stays empty for ConfigOptionSrc instances). """

    subs_dct: Dict[str,'ConfOrOptSrc'] = field(default_factory=dict)
    """ Dict version of self.elements. """

    #---------------------------------------------------------------------

    config_setter_path: Tuple[str] = None
    """
    "Path" to access the config holding this argument in CopiableConfig objects.
    This allows to modify them on the fly if needed (Lang, ...).
    """

    depth: int = None
    """
    Depth of the current instance in the ConfigSrc tree (used to rebuild indentations).
    """

    py_macros_path: str = None
    """
    Path of attributes to the current element, with "pyodide_macros" as source instead of "config".
    """

    long_accessor: bool = False
    """
    If True, the BaseMaestro getter name will be the complete path instead of using only
    the tail config property name.
    When assigned to a SubConfig object, it automatically transfers its value to its children.
    """

    #---------------------------------------------------------------------

    @property
    def get_md_link(self):
        return '#'+self.py_macros_path

    @property
    def indent(self) -> str :
        """ Computed because self.depth doesn't exist at init time. """
        return '    ' * self.depth


    def __str__(self):
        path_name = '.'.join((self.config_setter_path or ()) + (self.name,))
        return f"{ self.__class__.__name__ }({ path_name })"


    def get_children(self, action:Dumping):
        return self.elements


    def has(self, sub_name:str):
        """ Check if @sub_name is a sub element of the current object. """
        return sub_name in self.subs_dct



    def build_dynamic_config_class_name(self, name:str=""):
        """
        Convert the given name (or self.name) to the name of the concrete mkdocs.config.Config
        name built at runtime (through to_config)
        """
        name = name or self.name
        uppers = map(str.title, name.split('_'))       # split because pyodide_macros... x)
        return f"{ ''.join(uppers) }Config"


    def to_config(self):
        """
        Transform the current class hierarchy to an actual mkdocs plugin Config object,
        or a subitem of it. These are the objects that are holding the actual/concrete values.
        """
        raise NotImplementedError()












@dataclass
class CommonTreeSrcInternalBase(CommonTreeSrcBase, metaclass=ABCMeta):
    """ Layer dedicated to internal values and configuration. """

    is_config: bool = False
    """ True if the given object is a SubConfigSrc object """

    is_macro: bool = False
    """ True if the given object is a MacroConfigSrc object """

    is_plugin_config: bool = False
    """ True if the given object is a PluginConfigSrc object """

    is_message: bool = False
    """ Identify a ConfigOptionSrc related to a Lang message. """


    inclusion_profile: Dumping = Dumping.all
    """ Internal config to know in what situation to use or not the given element/object. """

    #---------------------------------------------------------------------
    # All these are using None, hence triggering failure if used at the wrong time (hopefully)...
    #       => `build_accessor` MUST HAVE BEEN RUN BEFORE USING THEM.
    is_in_config: Optional[bool] = None
    is_in_yaml_schema: Optional[bool] = None
    is_in_yaml_docs_tree: Optional[bool] = None
    is_in_signature: Optional[bool] = None
    is_in_args_tables: Optional[bool] = None
    is_in_docs_config: Optional[bool] = None

    INTERNALS: ClassVar[Set[str]] = set('''
        is_in_config
        is_in_yaml_schema
        is_in_yaml_docs_tree
        is_in_signature
        is_in_args_tables
        is_in_docs_config
    '''.split())


    def __post_init__(self):

        if any( getattr(self, prop) is not None for prop in self.INTERNALS):
            raise ValueError(
                f'Invalid definition of {self.name}: the `is_in_...` properties should never be '
                'defined manually: use the Dumping values.'
            )

        v = self.inclusion_profile

        self.is_in_config         = bool(v & Dumping.mkdocs_config)

        self.is_in_yaml_schema    = bool(v & Dumping.yaml_schema)
        self.is_in_yaml_docs_tree = bool(v & Dumping.yaml_docs_tree)

        self.is_in_signature      = bool(v & Dumping.macro_signature)
        self.is_in_args_tables    = bool(v & Dumping.macro_args_table)
        self.is_in_docs_config    = bool(v & Dumping.describe_in_docs_config)












@dataclass
class CommonTreeSrcDeprecated(CommonTreeSrcInternalBase, metaclass=ABCMeta):
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

    _KEEP_DEPRECATED_IN_PLUGIN_CONFIG: ClassVar[bool] = True


    deprecation_status: Optional[DeprecationStatus] = None
    """ Kind of deprecation. Also property of DeprecationTemplate namespace. """

    moved_to: str = ""
    """
    For DeprecationStatus.moved only: where to transfer the value.
    """


    @property
    def is_deprecated(self):
        """ True if the corresponding ConfigOption is deprecated """
        return bool(self.deprecation_status)


    def __post_init__(self):
        # Things that are not in the config or are deprecated should never be in the docs/yaml
        if self.is_deprecated:
            self.inclusion_profile = Dumping.config_and_internals

        super().__post_init__()

        if self.is_deprecated:
            if self.is_in_config != self._KEEP_DEPRECATED_IN_PLUGIN_CONFIG:
                raise PmtConfigurationError(
                    "Something suspicious happened: deprecated options should still be present "
                    f"in the plugin's config (see { self.name } inclusion_profile) "
                    "definition) to be included in the PyodideMacroConfig."
                )
            if self.deprecation_status is None:
                raise PmtConfigurationError(
                    "Deprecated options should have value set for the `deprecation_status` argument:"
                    f"({ self })"
                )


    def yield_invalid_yaml_paths_or_values(self, _value:Any=None, arg_only=False):
        if self.is_deprecated:
            path = self.name if arg_only else f"`{ self.py_macros_path[PMT_PM_PREFIX_SIZE:] }`"
            yield True, f"{ path } is deprecated and shouldn't be used anymore."












@dataclass
class CommonTreeSrcWithGetters(CommonTreeSrcDeprecated, metaclass=ABCMeta):

    def build_accessor(self, path: List[str], is_terminal=False):
        """
        Register the internal properties `config_setter_path`, and `maestro_extractor_getter_name`
        if @is_terminal is True.
        """
        self.py_macros_path     = '.'.join( ('pyodide_macros',*path[1:]) )
        self.config_setter_path = tuple(path[:-1])
        self.depth              = len(self.config_setter_path)
        if is_terminal:
            self._build_terminal_accessor(path)


    def _build_terminal_accessor(self, path: List[str]):
        """
        Triggers the creation of an actual ConfigExtractor configuration on the current object.
        The objects holding this value will get a matching getter on the BaseMaestro class.
        """
        getter = self.name
        if self.long_accessor:
            getter = '_'.join(path[1:])     # Excluding "pyodide_macros" path head

        self.maestro_extractor_getter_name = self.is_deprecated*'_' + getter












@dataclass
class CommonTreeSrcWithDocsOrYaml(CommonTreeSrcWithGetters, metaclass=ABCMeta):
    """ Generic behaviors about docs/yaml related data. """


    docs: str = ""
    """ Text to use when building the "summary" args tables in the docs """

    extra_docs: str = ''
    """
    Additional informations, added after the table when individual elements are displayed
    (see IDE-details.md)
    """

    yaml_desc: str=""
    """
    Short description that can used in place of self.docs here or there.
    If not given, self.docs is assigned to it.

    WARNING: HAS TO CONTAIN BARE/simple MARKDOWN => NO MACROS CALLS!
    """

    yaml_schema_dct: Optional[dict] = None
    """
    If defined, used when building the corresponding yaml schema dict, instead of computing it
    automatically.
    """

    docs_page_url: Path = None
    """
    In the form of a `Path`-like object, then used in the following way:

    ```python
    # docs_page_url = Path("relative_path/#anchor_template")
    str( site_url / docs_page_url ).format(
        name=self.name,
        py_macros_path=self.py_macros_path
    )
    ```

    WARNING: Usable ONLY for links internal to PMT docs.
    """

    schema_md_link: str = None
    """
    If given replace the one automatically built from site_url and self.docs_page_url when
    creating a link for the yaml schemas trees.
    """

    mkdocstrings_id: str=None
    """ String to build anchor_redirect for old mkdocstrings-like links... """


    DEFAULT_DOCS_URL_TEMPLATE: ClassVar[Path] = None
    """
    Used as default when the docs_page_url argument isn't provided.
    May be replaced on the fly from outside at declaration time, to ease definitions.
    """



    @classmethod
    def with_default_docs(cls, url:Path):
        """
        Method used at instances declaration time, to update more easily the value of the
        DEFAULT_DOCS_URL_TEMPLATE class level property.
        """
        CommonTreeSrcWithDocsOrYaml.DEFAULT_DOCS_URL_TEMPLATE = url
        return cls


    #------------------------------------------------------------------------------------


    def __post_init__(self):
        """
        Reformat and assign the docs and yaml_desc properties.
        """
        super().__post_init__()
        self.docs       = inline_md(self.docs, in_cell=True, validate=True)
        self.extra_docs = inline_md(self.extra_docs, validate=True) if self.extra_docs else ""
        self.yaml_desc  = inline_md(self.yaml_desc) if self.yaml_desc else self.docs or self.extra_docs

        if self.is_in_yaml_docs_tree or self.is_in_yaml_schema:

            if '{{' in self.yaml_desc and self.name!='j2_variable_start_string':
                raise PmtConfigurationError(
                    "`yaml_desc` shouldn't contain macros call:\n"
                   f"    { self } -> yaml_desc:\n        {self.yaml_desc!r}"
                )
            if '`#!py' in self.yaml_desc:
                raise PmtConfigurationError(
                    "`yaml_desc` shouldn't contain mkdocs python inline linting syntax: `#!py ...`"
                )

        if self.docs_page_url is None:
            self.docs_page_url = self.DEFAULT_DOCS_URL_TEMPLATE


    def build_accessor(self, path: List[str], is_terminal=False):

        super().build_accessor(path, is_terminal=is_terminal)

        # Prepare anchor_redirect for old mkdocstrings ids... x/
        #  pyodide_mkdocs_theme.pyodide_macros.plugin_config.IdesConfig.XXX
        re_path = [ 'pyodide_mkdocs_theme.pyodide_macros.plugin', *path ]

        is_pyodide_macro        = self.name == 'config'
        is_original_macros_prop = len(re_path)==3 and not self.is_config

        if not is_pyodide_macro and not is_original_macros_prop:
            re_path[2] = re_path[2].title() + 'Config'      # args -> ArgsConfig

        self.mkdocstrings_id = '.'.join(re_path)



    #----------------------------------------------------------------------------------------


    def get_yaml_schema_md_infos(self, site_url:Path) -> str:
        """ Build link toward the related documentation element in the configuration page. """

        if self.schema_md_link:
            txt = address = self.schema_md_link
        else:
            template = str( site_url / self.docs_page_url )
            txt = template.format(
                name = self.name,
                get_md_link = '#'+self.py_macros_path,
            )
            address = template.format(
                name = self.name,
                get_md_link = self.get_md_link,
            )
            # Restore double slash in  "http(s)://" (disappeared because of Path)
            txt,address = (re.sub(r'^(https?:/)', r'\1/', s) for s in (txt,address))

        return f"{ self.yaml_desc }\n\n[{ txt }]({ address })"












@dataclass
class CommonTreeSrc(
    CommonTreeSrcWithDocsOrYaml,
    CommonTreeSrcDeprecated,
    metaclass=ABCMeta
):
    """ Overall interface/class with common logic elements """
