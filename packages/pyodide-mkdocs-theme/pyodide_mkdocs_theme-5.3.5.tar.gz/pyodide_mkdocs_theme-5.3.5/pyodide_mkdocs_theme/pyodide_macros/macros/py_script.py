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
# pylint: disable=unused-argument, invalid-name, missing-module-docstring


import re
from pathlib import Path
from functools import wraps
from typing import Any, Tuple, TYPE_CHECKING, Type




from ..tools_and_constants import MACROS_WITH_INDENTS, ScriptData
from ..parsing import build_code_fence
from ..plugin.maestro_macros import MaestroMacros
from ..files_extractors.concrete_extractors import FileExtractor, PythonExtractor, SqlExtractor

if TYPE_CHECKING:
    from pyodide_mkdocs_theme.pyodide_macros import PyodideMacrosPlugin






def _more_code_fence(
    env: 'PyodideMacrosPlugin',
    content: str,
    title: str,
    attrs: str,
    no_block: bool,
    lang: str='python',
):
    """
    Extra function to centralize some of the formatting logic.
    """
    indent  = env.get_macro_indent()

    if no_block:
        return content.strip('\n').replace('\n', '\n'+indent)

    out = build_code_fence(
        content,
        indent,
        title=(title or ""),
        attrs=(attrs or ""),
        lang=lang,
    )
    return out






def section(env:MaestroMacros):
    """
    Insert the given section from the python file.

    Notes:
    * To use only on python scripts holding all the sections for the IDE macros. For regular
    files, use the `py` macro or regular code fences with file inclusions (for performances
    reasons).
    * This macro DOES NOT WORK with content built from different python files. Use the
    `composed_py` macro for this purpose.
    """
    MACROS_WITH_INDENTS.add('section')

    @wraps(section)
    def _section(
        py_name:      str,
        section_name: ScriptData,
        auto_title:   bool = None,              # False
        name_only:    bool = None,              # False
        title:        str = None,
        no_block:     bool = None,              # False
        attrs:        str = None,               # ""
        file:         str = None,               # 'python'
        ID: Any=None # sink (deprecated)        # pylint: disable=unused-argument
    ):
        kls = SqlExtractor if file=='sql' else PythonExtractor
        _, file_data = kls.get_file_extractor_for(env, py_name, allow_snippets_py=True)
        content = file_data.get_section(section_name)

        if not title and auto_title:
            title = file_data.exo_file.name if name_only else py_name

        out = _more_code_fence(env, content, title, attrs, no_block, lang=file)
        return out

    return _section





def composition_factory(env:MaestroMacros, func, ExtractorClass:Type[FileExtractor], lang:str):

    MACROS_WITH_INDENTS.add(func.__name__)

    @wraps(func)
    def _composed(
        exo_name:     str,
        sections:     str  = None,      # ""
        with_headers: bool = None,      # True
        auto_title:   bool = None,      # False
        name_only:    bool = None,      # False
        title:        str  = None,      # ""
        attrs:        str  = None,      # ""
        no_block:     bool = None,      # False
    ):
        _, extractor = ExtractorClass.get_file_extractor_for(env, exo_name, allow_snippets_py=True)
        targets = re.split(r"[\s,;]+", sections) if sections else ScriptData.VALUES
        content = extractor.get_sections(targets, with_headers)

        if not title and auto_title:
            title = extractor.exo_file.name if name_only else exo_name

        out = _more_code_fence(env, content, title or "", attrs or "", no_block, lang)
        return out

    return _composed




def composed_py(env:MaestroMacros):
    """
    Generalization of the `section` macro, when using inclusion instructions with different
    python files.

    * By default, all normal PMT sections are displayed (ignoring extras).
    *if @full is True, all existing sections are displayed.
    """
    return composition_factory(env, composed_py, PythonExtractor, 'python')



def composed_sql(env:MaestroMacros):
    """
    Generalization of the `section` macro, when using inclusion instructions with different
    SQL files.

    * By default, all normal PMT sections are displayed (ignoring extras).
    * if @full is True, all existing sections are displayed.
    """
    return composition_factory(env, composed_sql, SqlExtractor, 'sql')






def py(env:MaestroMacros):
    """
    Macro python rapide, pour insérer le contenu d'un fichier python. Les parties HDR sont
    automatiquement supprimées, de même que les tests publics (cf. Pyodide-Mkdocs).
    Pour tout autre fichier python, tout le contenu est inséré automatiquement (notamment,
    pour les fichiers du thème !).

    Si l'argument @stop est fourni, ce doit être une chaîne de caractères compatible avec
    `re.split`, SANS matching groupes. Tout contenu après ce token sera ignoré (token compris)
    et "strippé".
    """
    MACROS_WITH_INDENTS.add('py')

    @wraps(py)
    def wrapped(
        py_name: str,
        stop:str=None,
        *,
        auto_title: bool = None,      # False
        name_only:  bool = None,      # False
        title:      str  = None,      # ""
        attrs:      str  = None,      # ""
        no_block:   bool = None,      # False
        **_
    ) -> str:
        return script(
            env,
            py_name,
            stop = stop,
            auto_title = auto_title,
            name_only = name_only,
            title = title,
            attrs = attrs,
            no_block = no_block,
        )
    return wrapped




def script(
    env: MaestroMacros,
    py_name: str,
    *,
    stop= None,
    auto_title: bool = None,      # False
    name_only:  bool = None,      # False
    title:      str  = None,      # ""
    attrs:      str  = None,      # ""
    no_block:   bool = None,      # False
) -> str:
        """
        Renvoie le script dans une balise bloc avec langage spécifié

        - lang: le nom du lexer pour la coloration syntaxique
        - nom: le chemin du script relativement au .md d'appel
        - stop: si ce motif est rencontré, il n'est pas affichée, ni la suite.
        """
        target = env.get_sibling_of_current_page(py_name, tail='.py')
        _, content, public_tests = env.get_hdr_and_public_contents_from(target)

        # Split again if another token is provided
        if stop is not None:
            # rebuild "original" if another token is provided
            if public_tests:
                content = f"{ content }{ env.lang.tests.msg }{ public_tests }"
            content = re.split(stop, content)[0]

        if not title and auto_title:
            py_name += '.py'
            title = Path(py_name).name if name_only else py_name

        out = _more_code_fence(env, content, title, attrs, no_block)
        return out
