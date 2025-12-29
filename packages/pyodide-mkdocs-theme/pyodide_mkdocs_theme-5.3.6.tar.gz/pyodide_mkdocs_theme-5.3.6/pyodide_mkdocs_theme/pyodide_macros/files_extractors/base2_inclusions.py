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
from typing import ClassVar, Dict, List, Set, Tuple

from ..exceptions import (
    PmtCircularPyInclusionError,
    PmtPythonPyInclusionError,
)
from ._inclusions_tools import InclusionConfig
from .base1_contents_extractor import BasePmtSectionsExtractor


CWD = Path.cwd()











@dataclass(eq=False)
class FileExtractorWithInclusions(BasePmtSectionsExtractor):
    """
    Manage inclusions in the python files, following this kind of syntaxes:

        ## {{ [md]py_name:section:section }}
        ## {{ [py]py_name:section:section }}
        ## {{ py_name:section:section }}

    Relative paths usable:
        ## {{ ../bal/py_name:section }}
        ## {{ :section }}                      (= "in the current py file")

    Possible to change the file extractor type on the fly by giving the extension file in py_name.
    """

    _children_by_sections: Dict[str, List[InclusionConfig]] = None
    """
    Children of this "file", by sections as: {section: [InclusionConfig, ...]}
    """

    INCLUSION_PATTERN: ClassVar[re.Pattern] = None

    INCLUSION_HEADER: ClassVar[str] = None
    """ Leading element of the inclusions delimiter token. Defined by children classes. """

    #----------------------------------------------------------------------------

    INCLUSIONS_SET: ClassVar[Set[ Tuple[Path,str] ]] = set()
    """ Current inclusion path, to spot cyclic dependencies. """

    INCLUSIONS_PATH: ClassVar[List[ Tuple[Path,str] ]] = []
    """
    Current inclusion path, to spot cyclic dependencies.
    The first element is always the current md file src_uri, the others subsequent elements being
    (Extractor.exo_file, section). Also needed for logging/error message purpose.
    """

    #----------------------------------------------------------------------------


    def get_current_md(self):
        """ When resolving a section inclusion, allow to get data about the current step. """
        return self.INCLUSIONS_PATH[0][0]

    def get_src_file(self):
        """ When resolving a section inclusion, allow to get data about the current step. """
        return self.INCLUSIONS_PATH[1][0]

    def get_current_file(self):
        """ When resolving a section inclusion, allow to get data about the current step. """
        return self.INCLUSIONS_PATH[-1][0]

    def get_current_section(self):
        """ When resolving a section inclusion, allow to get data about the current step. """
        return self.INCLUSIONS_PATH[-1][1]


    @classmethod
    def build_inclusions_pattern(cls):
        pattern = (
            r"(?P<indent>[ \t]*)"
            rf"{ cls.INCLUSION_HEADER }\s*{ '{{' }\s*"
            r"(?P<src>\[\w+\])?"
            r"(?P<rel_path>[^:\s]*)"
            r"(?P<targets>[^\}]+?)\s*"
            r"\}\}"
        )
        return re.compile(pattern)



    def extract_contents(self):
        """
        Recursively create/extract the contents of individual files.
        This builds the dependency graph internally (-> self._children), but doesn't apply the
        injections.
        Since the IdeFilesExtractor instances are cached, this step will always terminate, as
        long as the inclusions aren't resolved.
        """
        self.extract_files_content()       # No super call: would raise by contract

        self._children_by_sections = {
            section: self.build_inclusions(content)
            for section, content in self.contents.items()
        }


    def build_inclusions(self, content:str):
        inclusions = []
        for m in self.INCLUSION_PATTERN.finditer(content):
            i = m.start(0)
            if i and content[i-1] != '\n':
                raise PmtPythonPyInclusionError(
                    "An inclusion instruction should never have text on its left.\n"
                    f"    Found this misplaced instruction: { m[0] }\n"
                    f"    File: { self.exo_file }\n"
                )
            inclusions.append(InclusionConfig.build_for(self, m))

        return inclusions


    def get_section(self, section):
        empty = not self.contents[section] if section in self.contents else section in self.env.allowed_pmt_sections
        if empty:
            return ""

        self.INCLUSIONS_SET.clear()
        self.INCLUSIONS_PATH.clear()
        self.INCLUSIONS_PATH.append( (Path(self.env.page.file.abs_src_path).relative_to(CWD),'') )
        resolved = self.resolve_section_inclusions(section)
        return resolved


    def resolve_section_inclusions(self, section:str) -> str:
        """
        Actually resolve the inclusions to build the final content for the given section.

        WARNING: this resolution must NEVER call/use `extractor.get_section(...)`, because the
        very first (outer) call does not require the section to exist, while its definition is
        mandatory when resolving inclusions.
        """

        location = self.docs_file, section
        self.INCLUSIONS_PATH.append(location)           # Done first, to build full error messages
        self.validate_section(section, required=True)

        if location in self.INCLUSIONS_SET:
            trace = self.get_inclusion_trace()
            raise PmtCircularPyInclusionError(
                "Cannot resolve python files inclusions because a circular reference has "
                f"been found.{ trace }"
            )
        self.INCLUSIONS_SET.add(location)

        content = self.contents[section]
        if section in self._children_by_sections:
            to_apply = self._children_by_sections[section]
            for inclusion in to_apply:
                content = inclusion.apply(content)

        self.INCLUSIONS_SET.remove(location)
        self.INCLUSIONS_PATH.pop()

        return content


    @classmethod
    def get_inclusion_trace(cls):
        full_path = cls.INCLUSIONS_PATH
        order = ''.join(
            f"\n    { file }{ ': '*bool(section) }{ section }" for file,section in full_path
        )
        return f"\nThe files resolution order up to this error is as follow:{ order }"
