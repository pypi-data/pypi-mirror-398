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

from dataclasses import dataclass
from typing import ClassVar, TYPE_CHECKING

from mkdocs.config import config_options as C


from ..messages.classes import Msg, MsgPlural, MultiLangDataDict, TestsToken, Tip, get_tr_and_multi_lang_dct
from ..exceptions import PmtInternalError
from ..tools_and_constants import Dumping, Language, TermFormat
from .config_option_src import ConfigOptionNumber
from .plugin_config_src import SubConfigSrc, ConfigOptionSrc

if TYPE_CHECKING:
    from ..plugin.pyodide_macros_plugin import PyodideMacrosPlugin







@dataclass
class ConfigMsgSrc(ConfigOptionSrc):

    current_value_access:str = ''

    def build_accessor(self, path):
        super().build_accessor(path)
        self.current_value_access = self.py_macros_path.replace('pyodide_macros','env')


    def get_default_or_live_env_default(self, env:'PyodideMacrosPlugin'):
        return eval(self.current_value_access, {'env':env})


@dataclass
class ConfigEmSrc(ConfigMsgSrc, ConfigOptionNumber): pass




@dataclass
class LangConfigSrc(SubConfigSrc):
    """
    SubConfigSrc element defining one Lang element, with it's msg, plural, width, ... infos.

    These objects DO NOT behave in the same way others do:
    - They generate their ConfigOption children automatically
    - The yaml tree is defined as usual
    - But the MkDocs config dump and Maestro getter actually stop at the sub config level,
      returning a ConfigStr instance, so that extra properties needed for backward compatibility
      are present.

    This also means the meta/yal config updates are handled in a different way when merging the
    data with for the MetaTree objects/logistic.
    """

    is_message: bool = True

    TOP_LANG_NAME: ClassVar[str] = 'lang'

    def get_children(self, action):
        if self.name != self.TOP_LANG_NAME and action == Dumping.docs_summary_table:
            return ()
        return super().get_children(action)

    @property
    def default(self):
        """ Override specifically for the docs config summary """
        return [...]

    @property
    def get_md_link(self):
        if self.name != self.TOP_LANG_NAME:
            return '--messages-details'
        return "#"+self.py_macros_path


    @classmethod
    def build_hierarchy(cls, lang:Language=Language.fr):

        multi_lang_data_dct = get_tr_and_multi_lang_dct()
        elements = tuple(
            cls.build_tr_src_elements(name, multi_lang_data_dct) for name in multi_lang_data_dct
        )

        out = cls(
            cls.TOP_LANG_NAME,
            elements = elements,
            inclusion_profile = Dumping.not_in(Dumping.maestro_getters),
            extra_docs = """
                Configuration des différents messages utilisés ici et là dans le site construit.
                Voir la page concernant [les messages](--messages-details) du thème pour plus
                d'informations.

                {{ pmt_note("Nota : les valeurs par défaut indiquées ici et là pour les messages dans
                la documentation font parfois apparaître des caractères unicodes à la place de certains
                accents. Ceci est essentiellement dû à la conversion automatique des contenus lorsque
                la documentation est générée. On peut tout à fait utiliser des accents ou des caractères
                spéciaux dans les messages.", lf_location=0)}}
            """,
            yaml_desc="""
                Configuration of the various messages used here or there in the build site.
            """
        )
        return out


    @classmethod
    def build_tr_src_elements(cls, name:str, multi_lang_data_dct: MultiLangDataDict):

        data = multi_lang_data_dct[name]
        desc = data.en

        generic_props = dict(is_optional=True, long_accessor=True)
        msg  = ConfigMsgSrc('msg', str, yaml_desc=desc, **generic_props)
        form = ConfigMsgSrc(
            'format', str, **generic_props,
            conf_type=C.Choice(TermFormat.VALUES),
            yaml_desc="Formatting of the message in the terminal.",
        )

        elements = (
            msg, form,
        ) if isinstance(data.src, Msg) else (
            msg, ConfigMsgSrc('plural', str, **generic_props), form,
        ) if isinstance(data.src, MsgPlural) else (
            msg,
            ConfigEmSrc('em', yaml_desc="Tooltip width (em)", **generic_props),
            ConfigMsgSrc('kbd', str, **generic_props, yaml_desc="Keyboard shortcut (informational purpose only)"),
        ) if isinstance(data.src, Tip) else (
            msg,
        ) if isinstance(data.src, TestsToken) else (
            None    # (no coma here! -> not a tuple)
        )

        if elements is None:
            raise PmtInternalError(f"Unknown element for {name}: ")

        return cls(
            name, str,
            is_message = True,
            yaml_desc  = desc,
            elements   = elements,
            inclusion_profile = Dumping.not_in(Dumping.maestro_getters, Dumping.describe_in_docs_config),
        )
