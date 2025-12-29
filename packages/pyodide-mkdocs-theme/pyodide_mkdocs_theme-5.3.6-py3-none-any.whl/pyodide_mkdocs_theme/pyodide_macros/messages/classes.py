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
import ast
from pathlib import Path
from textwrap import dedent
from argparse import Namespace
from dataclasses import dataclass
from typing import ClassVar, Dict, Optional, Tuple, Type, Union, TYPE_CHECKING

from ..exceptions import PmtCustomMessagesError, PmtInternalError
from ..tools_and_constants import Language, MultiLang

if TYPE_CHECKING:
    from ..plugin import PyodideMacrosPlugin
    from .fr_lang import LangFr



TMP_PATTERN  = re.compile('')       # Temp definition (done this way for linting and mkdocstrings... :/ )


Tr = Union['Msg', 'MsgPlural', 'Tip', 'TestsToken']

DocStr = str
LangProp = str
DocStringsDict = Dict[Language, Dict[str,DocStr]]
MultiLangDataDict = Dict[str, MultiLang[DocStr,Tr] ]



@dataclass
class DumpedAsDct:
    """ Base class to automatically transfer "lang" messages from python to JS """
    # pylint: disable=no-member,missing-function-docstring

    ENV: ClassVar['PyodideMacrosPlugin'] = None
    PROPS: ClassVar[Tuple[str,...]] = ()

    def __str__(self):
        return self.msg

    def dump_as_dct(self):
        out = {
            prop: val if isinstance(val, (int,float)) else  str(val)
                for prop in self.PROPS
                if (val:=getattr(self, prop)) is not None
        }
        return out



@dataclass
class Message(DumpedAsDct):
    """
    Intermediate class so that Msg and MsgPlural are sharing a specific class in their mro.
    """


@dataclass
class Msg(Message):
    """
    A simple message to display in the application.

    Parameters:
        msg:    Message to use
        format: Formatting to use in the terminal. See lower.
    """
    PROPS: ClassVar[Tuple[str,...]] = 'msg', 'format'

    msg: str = None
    format: Optional[str] = None


@dataclass
class MsgPlural(Message):
    """
    A message that could be used in singular or plural version at runtime.

    Parameters:
        msg:    Message to use
        plural: If not given, `msg+"s"` is used as plural.
        format: Formatting to use in the terminal. See lower.
    """
    PROPS: ClassVar[Tuple[str,...]] = 'msg', 'format', 'plural'
    msg:    str = None
    plural: str = None
    format: Optional[str] = None

    def __post_init__(self):
        if self.plural is None:
            self.plural = self.msg+'s'

    def one_or_many(self, many:bool):
        return self.plural if many else self.msg




@dataclass
class Tip(DumpedAsDct):
    """
    Data for tooltips.

    Parameters:
        em:     Width of the tooltip element, in em units (if 0, use automatic width).
        msg:    Tooltip message.
        kbd:    Keyboard shortcut (as "Ctrl+I", for example). Informational only (no
                impact on the behaviors)

    If a `kbd` combination is present, it will be automatically added in a new line
    after the tooltip `msg`.
    """
    PROPS: ClassVar[Tuple[str,...]] = 'msg', 'em', 'kbd'

    em: int   = 0       # Width, in em. If 0, use automatic width
    msg: str = None     # tooltip message
    kbd: str = ""       # ex: "Ctrl+I" / WARNING: DO NOT MODIFY DEFAULTS!

    def __str__(self):
        """
        Keep this part of the logic fully dynamic, even if "costy", because the lang.tests
        value _might_ change on the fly, even with the default value for the tips.
        """
        msg  = self.msg
        deps = ()
        if '{site_name}' in msg:
            deps += (lambda env: ('site_name', env and env.site_name), )
        if '{tests}' in msg:
            deps += (lambda env: ('tests', env and env.lang.tests), )
        if deps:
            msg = msg.format(**dict(func(self.ENV) for func in deps))
        if self.kbd:
            kbd = re.sub(r"(\w+)", r"<kbd>\1</kbd>", self.kbd)
            msg = f"{ msg }<br>({ kbd })"
        return msg

    def dump_as_dct(self):
        dct = super().dump_as_dct()
        dct['msg'] = str(self)      # Enforce the message is complete/fully handled (see above)
        return dct





@dataclass
class TestsToken(DumpedAsDct):
    """
    Specific delimiter used to separate the user's code from the public tests in an editor.
    Leading and trailing new lines used here will reflect on the editor content and will
    match the number of additional empty lines before or after the token itself.

    Because this token is also be converted to a regex used in various places, it has to
    follow some conventions. ___Ignoring leading and trailing new lines:___

    - The string must begin with `#`.
    - The string must not contain internal new line characters.
    - Ignoring inner spaces, the token string must be at least 6 characters long.

    Parameters:
        msg:  Separator to use (with leading and trailing new lines).

    Raises:
        PmtCustomMessagesError: If one of the above conditions is not fulfilled.
    """
    PROPS: ClassVar[Tuple[str,...]] = 'msg',

    msg: str = None

    _as_pattern: re.Pattern = None

    def __post_init__(self):
        self._as_pattern = self._define_pattern()

    @property
    def as_pattern(self):
        if not self._as_pattern:
            self._define_pattern()
        return self._as_pattern

    def _define_pattern(self):
        s = self.msg.strip()
        short = s.replace(' ','').lower()

        if not s.startswith('#'):
            raise PmtCustomMessagesError(
                "The public tests token must start with '#'"
            )
        if '\n' in s:
            raise PmtCustomMessagesError(
                "The public tests token should use a single line"
                " (ignoring leading or trailing new lines)"
            )
        if short=='#test' or len(short)<6:
            raise PmtCustomMessagesError(
                "The public tests token is too short/simple and could cause false positives."
                " Use at least something like '# Tests', or something longer."
            )

        pattern = re.sub(r'\s+', r"\\s*", s)
        return re.compile('^'+pattern, flags=re.I)

    def __str__(self):
        return self.msg.strip()

    def dump_as_dct(self):
        return {'msg': f"\n{ self.msg }\n", 'as_pattern': self.as_pattern.pattern}









class LangBase(Namespace):
    """ Generic behaviors for Lang classes """


    __LANG_CLASSES: ClassVar[ Dict[str,Type['LangFr']] ] = {}
    """
    Automatically registered subclasses.
    """

    def __init_subclass__(cls) -> None:
        if not cls.__name__.startswith('Lang'):
            raise PmtInternalError(
                "All LangBase subclasses should be named `LangX`, starting with `Lang`, "
                f"but found: { cls.__name__ }"
            )
        name = cls.__name__[4:].lower() or 'fr'
        LangBase.__LANG_CLASSES[name] = cls
        super().__init_subclass__()



    @staticmethod
    def get_lang(lang:Language):
        return LangBase.__LANG_CLASSES[lang]


    @staticmethod
    def get_langs_dct():
        """
        Return a fresh dict of fresh Lang instances (to make sure no side effects are possible,
        especially because of overloads).
        """
        dct = { name: kls() for name,kls in LangBase.__LANG_CLASSES.items() }
        return dct














def get_tr_and_multi_lang_dct() -> MultiLangDataDict:
    """
    Build a dict of MultiLang objects, representing the various language data for one property.

        MultiLangDataDict = Dict[PropName, MultiLang[DocStr,Tr] ]
    """

    def get_ast_tree_and_lang_from_file(file:Path):
        lang = Language.get_lang_from_filename(file)
        code = file.read_text(encoding='utf-8')
        tree = ast.parse(code)
        return lang, tree


    def find_Lang_class_definition(tree:ast.Module):
        return next(
            kls for kls in ast.walk(tree)
                if isinstance(kls, ast.ClassDef) and kls.name.startswith("Lang")
        )

    def get_doc_string_or_empty_str_from_expr_ast(node: Optional[ast.Expr]):
        """
        Extract the docstring for a message in a Lang class.
        """
        if node and isinstance(node, ast.Expr):
            return dedent(node.value.value.strip('\n')).strip()
        return ""

     #-----------------------------------------------------------------------------------

    all_lang_files = [
        Path(__file__).parent / f"{ lang }{ Language.LANG_FILE_SUFFIX }" for lang in Language.VALUES
    ]

    # Build a dict of lang -> prop_name -> docstring:
    docstrings_dct: DocStringsDict = {}
    for file in all_lang_files:
        lang, tree = get_ast_tree_and_lang_from_file(file)
        lang_ast   = find_Lang_class_definition(tree)
        docs = {
            node.target.id : doc
                for i,node in enumerate(lang_ast.body)
                if isinstance(node, ast.AnnAssign) and (
                    doc := get_doc_string_or_empty_str_from_expr_ast( i+1<len(lang_ast.body) and lang_ast.body[i+1] )
                )
        }
        docstrings_dct[lang] = docs


    # Check definitions consistency:
    ref  = set(docstrings_dct[Language.fr])
    bads = [
        (lang, ref-oops, oops-ref) for lang,d in docstrings_dct.items() if ref != (oops:=set(d))
    ]
    if bads:
        tab = '\n\t'
        msg = 'Invalid Lang content: some classes are missing some docstrings:\n' + '\n\n'.join(
            f"{ lang.capitalize() }:\nMissing:\n\t{ tab.join(missing) }\nExtras:\n\t{ tab.join(extras) }"
            for lang, missing, extras in bads
        )
        raise ValueError(msg)


    # Convert a DocStringsDict to a Dict[ PropName, MultiLang[DocStr,Tr] ]
    Lang = LangBase.get_lang(Language.fr)
    multi_lang_dct: MultiLangDataDict = {}
    for name in Lang.__annotations__:
        src = getattr(Lang, name)
        multi_doc: MultiLang[DocStr] = MultiLang(
            *(
                docstrings_dct[lang][name] for lang in Language.VALUES
            ),
            src
        )
        multi_lang_dct[name] = multi_doc

    return multi_lang_dct
