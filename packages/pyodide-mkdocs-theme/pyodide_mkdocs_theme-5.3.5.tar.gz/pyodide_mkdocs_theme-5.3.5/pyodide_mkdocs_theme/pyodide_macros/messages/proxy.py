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


import json
from dataclasses import dataclass
from typing import Dict, TYPE_CHECKING, Optional

from ..pyodide_logger import logger
from ..parsing import camel
from ..plugin_tools.maestro_tools import dump_as_dct_with_camel_case
from .classes import DumpedAsDct, LangBase, LangProp, Msg, MsgPlural, TestsToken, Tip, Tr
from .fr_lang import LangFr as Lang

if TYPE_CHECKING:
    from ..plugin import PyodideMacrosPlugin








class TrProxy(DumpedAsDct):
    """
    WARNING: No @dataclass decoration here, despite the inheritance chaining: the automatic
             __init__ assignments ARE NOT DESIRED for the proxy logic!
    """

    message:str = ""

    # Override dataclass __init__ to avoid defining all property setters:
    def __init__(self, *_, message:str=None):
        self.message = message


    def _extract(self, prop:str, *, with_default=True, default_only=False):
        val = None if default_only else getattr(getattr(self.ENV.config.lang, self.message), prop)
        if val is None and with_default:
            lang = self.ENV.language
            val = getattr(getattr(LangBase.get_lang(lang), self.message), prop)
        return val

    @property
    def msg(self):
        return self._extract('msg')



class MsgProxy(TrProxy, Msg):

    @property
    def format(self):
        return self._extract('format')



class MsgPluralProxy(TrProxy, MsgPlural):

    @property
    def format(self):
        return self._extract('format')

    @property
    def plural(self):
        value = self._extract('plural', with_default=False)
        if value is None:
            msg = self._extract('msg', with_default=False)
            if msg is not None:
                value = msg+"s"
            else:
                value = self._extract('plural', default_only=True)
        return value



class TipProxy(TrProxy, Tip):

    @property
    def em(self):
        return self._extract('em')

    @property
    def kbd(self):
        return self._extract('kbd')



class TestsTokenProxy(TrProxy, TestsToken):

    # Skip super call, to avoid defining _as_pattern on the proxy object.
    def __post_init__(self): pass

    @property
    def as_pattern(self):
        """ Always computed dynamically. """
        return self._define_pattern()











@dataclass
class LangProxy:
    """ Relay class, extracting the config values on the fly. """

    env: 'PyodideMacrosPlugin' = None


    def __post_init__(self) -> 'LangProxy' :
        logger.info("Initialize Languages messages.")
        DumpedAsDct.ENV = self.env


    def overload(self, dct: Dict[LangProp,Tr]):
        """
        Overloads the defaults with any available user config data. This is done at macro
        registration time (= in a `define_env(env)` function, during the `on_config` event).
        """
        if dct:
            logger.info("Overloading messages.")
            for prop,tr in dct.items():
                dct  = tr.dump_as_dct()
                conf: Dict = self.env.config.lang[prop]
                conf.update(dct)


    @classmethod
    def dump_as_str(cls, env:Optional['PyodideMacrosPlugin']):
        """
        Create a complete json object with all the string representations of all the messages.
        - Takes potential overloads in consideration
        - If obj is None, use null for all values.
        """
        proxy: LangProxy = env and env.lang
        converter = (lambda _:None) if not env else proxy._to_dct
        dct = dump_as_dct_with_camel_case(Lang.__annotations__, proxy, converter)
        if env:
            out = json.dumps(dct)
        else:
            out = json.dumps(dct, indent=8).replace('"','')        # config-lib.js dump extra presentation
        return out


    def _to_dct(self, tr:Optional[Tr]):
        return tr and tr.dump_as_dct()



# Define all the LangProxy attributes:
for prop in Lang.__annotations__:
    cls_name  = getattr(Lang, prop).__class__.__name__
    proxy_cls = globals()[f'{ cls_name }Proxy']
    tr = proxy_cls(message=prop)
    setattr(LangProxy, prop, tr)
