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
# pylint: disable=multiple-statements, missing-function-docstring


import re
from pathlib import Path
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Literal, Tuple, TYPE_CHECKING, Union


from ..exceptions import PmtMacrosInvalidPmtFileError
from ..tools_and_constants import ScriptData
from ..parsing import add_indent
from ..indent_parser import IndentParser


if TYPE_CHECKING:
    from .concrete_extractors import FileExtractor


CWD = Path.cwd()














class InclusionParser(IndentParser):
    """
    Parser dedicated to analyze the sections and replacements instructions for inclusions (it does
    not handle the full instruction!).
    """

    _CACHE: ClassVar[Dict[str,List]] = {}

    LOOKING_FOR: ClassVar[str] = "python inclusions informations"

    targets: List[ScriptData]
    replacements: List[Tuple[str,str]]


    def gathered_data_as_str(self):
        replacements = ''.join(
            f"\n               {src!r} -> {repl!r}" for src,repl in self.replacements
        ) or "\n               ()"
        return f"""\
Content parsed:     {self.content!r}
Targeted sections:
               { ', '.join(self.targets) or () }
Replacements:{ replacements }"""


    def start_parsing(self):
        self.targets = []
        self.replacements = []

        while self.is_(':'):
            self.eat_section()

        if '*' in self.targets and len(self.targets) > 1:
            self.fatal("Cannot use '*' in combination with other section names.")

        while self.is_('[|]'):
            self.eat_replacement()

        if self.tokens_left():
            got_repl = bool(self.replacements)
            self.eat('[|]'if got_repl else '[:|]')

        return self.targets, self.replacements


    def eat_section(self):
        self.eat()
        is_all  = self.is_('[*]')
        section = self.eat() if is_all else self.eat_id()
        self.targets.append(section)

    def eat_replacement(self):
        self.eat()
        src = self.eat_repl_segment()
        self.eat_arrow()
        repl = self.eat_repl_segment()
        self.replacements.append((src,repl))

    def eat_arrow(self):
        i = self.i
        arrow = ''.join( self.tokens[i:i+2] )
        if arrow != "->":
            show = repr(arrow) if arrow else 'EOF'
            self.fatal(
                f"Expected an arrow `->` to specify the replacement to use, but found { show }"
            )
        self.eat()
        self.eat()

    def eat_repl_segment(self):
        if self.is_string():
            return self.eat_string()
        else:
            return self.eat_id()


    def eat_id(self):
        return self.eat(r'\w+')

    def eat_string(self):
        i = self.i
        self.err_stack_opening()
        self._eat_until_paired()
        self.err_stack_closing()
        j = self.i
        str_repr = ''.join(self.tokens[i:j])
        return eval(str_repr)


INCLUSION_PARSER = InclusionParser()














@dataclass
class InclusionConfig:
    """ Regroup the data for one inclusion instruction """

    ALL_SECTIONS: ClassVar[List[str]] = ['*']

    parent: 'FileExtractor' = None

    inclusion_instruction: str = None
    """
    Full inclusion instruction as string (with leading indent). Used to make the strings substitutions.
    """

    indent: str = ""
    """ Leading indentation level, as string. """

    redirection: str = ""
    """ Redirection instruction (may be empty string) """

    rel_path: str = ""
    """ Relative path to the file targeted to resolved this inclusion. """

    targets: List[Union[ScriptData, Literal['*']]] = None
    """
    List of children sections name to insert (in order). May be '*' if all sections of the target file
    must be included (using default sections ordering).
    """

    replacements: Dict[str,str] = None
    """ Replacements to apply after resolving the inclusions. """




    @classmethod
    def build_for(cls, parent:'FileExtractor', m:re.Match):
        """
        Build the InclusionConfig instance for the given parent Extractor, with the given match object.
        """
        indent, src, rel_path, targets_str = m['indent'], m['src'], m['rel_path'], m['targets']

        targets, replacements = INCLUSION_PARSER.parse(targets_str.strip(), parent.exo_file)

        return cls(parent, m[0], indent, src, rel_path, targets, replacements)



    def get_child_target_sections(self, child:'FileExtractor'):
        """
        No validation at this step, just produce the list of expected sections to include.
        Resolve the `*` case on the way.
        """
        if self.targets == self.ALL_SECTIONS:
            return [
                section for section in self.parent.env.allowed_pmt_sections_in_order
                        if section in child.contents
            ]
        return self.targets


    def apply(self, content:str):

        child   = self.get_child()
        targets = self.get_child_target_sections(child)

        sub_content = "\n\n".join(
            child.resolve_section_inclusions(child_section) for child_section in targets
        )

        for src,repl in self.replacements:
            sub_content = sub_content.replace(src,repl)

        indented = add_indent(sub_content, self.indent, leading=True)
        content  = content.replace(self.inclusion_instruction, indented)
        return content



    def get_child(self):
        """
        Extract the correct target/child file for the current inclusion/page/macro.

        Raise PmtMacrosInvalidPmtFileError if:
        - `rel_path` is not given (unless the redirection is `[py]`).
        - or if no target file can be found (whatever the way it is sought for: "by exercice" or
          "by chapter" modes).
        """
        redirect = self.redirection
        rel_path = self.rel_path

        if not redirect and not rel_path:        # Include a section from the current file
            return self.parent

        elif redirect=='[md]':
            source = self.parent.get_current_md()

        elif redirect in ('[py]', '[src]'):
            source = self.parent.get_src_file()
            if not rel_path:
                rel_path = source.stem

        elif redirect=='[cwd]':
            md = self.parent.get_current_md()
            source = CWD / md.stem

        else:
            source = self.parent.exo_file


        if not rel_path:
            raise PmtMacrosInvalidPmtFileError(
                "Inclusions using `[md]` or `[cwd]` require to specify a relative path information "
                f"(aka, `py_name`).\nOccurred in:\n{ self.parent.env.log() }"
            )

        as_path = Path(rel_path)
        tail    = as_path.suffix or self.parent.EXTENSION
        if as_path.suffix and rel_path.endswith(tail):
            rel_path = rel_path[:-len(tail)]

        runner_file = self.parent.env._get_sibling(source, rel_path, tail=tail)

        if not runner_file:
            raise PmtMacrosInvalidPmtFileError(
                f"No file matching {(redirect or '')+rel_path!r} could be found, starting from "
                f"the { source.parent } directory."
            )

        _, child = self.parent.get_file_extractor_for(
            self.parent.env, rel_path, runner_file=runner_file, allow_snippets_py=True
        )
        return child
