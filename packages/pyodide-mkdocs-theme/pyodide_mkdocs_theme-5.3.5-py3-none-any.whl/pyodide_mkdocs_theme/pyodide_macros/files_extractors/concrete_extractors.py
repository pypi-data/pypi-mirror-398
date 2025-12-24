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

from typing import TYPE_CHECKING, ClassVar, List, Optional, Tuple, Type
from pathlib import Path
from dataclasses import dataclass


from ..exceptions import PmtMacrosInvalidPmtFileError
from ..tools_and_constants import ScriptData, SiblingFile
from ..paths_utils import read_file
from .base3_generic_extractors import (
    GenericExtractor,
    SingleFileExtractor,
    SingleFileExtractorWithRems,
)

if TYPE_CHECKING:
    from pyodide_mkdocs_theme.pyodide_macros import PyodideMacrosPlugin

CWD = Path.cwd()







@dataclass(eq=False)
class FileExtractor(GenericExtractor):
    """
    Generic entry point: this class allow to spot automatically what is the class to use,
    whatever the original class is.
    """

    @classmethod
    def get_file_extractor_for(
        cls,
        env: 'PyodideMacrosPlugin',
        rel_path: str,
        *,
        runner_file: Optional[Path] = None,
        allow_snippets_py: bool = False,
    ) -> Tuple[Path, 'GenericExtractor'] :
        """
        Centralize the logic to pick the correct extractor subclass.
        If rel_path holds an extension/suffix, use it to determine the Extractor's type to use,
        overriding the current class type. Otherwise, work with the current class.
        """
        ExtractorClass: Type[FileExtractor] = cls
        as_path = runner_file or rel_path and Path(rel_path)

        if as_path:

            if as_path.suffix:
                ExtractorClass = cls.EXTENSION_TO_EXTRACTOR_CLASS[as_path.suffix]
            if rel_path and as_path.suffix:
                rel_path = rel_path[:-len(as_path.suffix)]

            extract_py  = ExtractorClass is PythonExtractor
            is_snippets = as_path.stem == env.py_snippets_stem

            if extract_py and is_snippets:
                ExtractorClass = PythonSnippetsExtractor
                if not allow_snippets_py:
                    raise PmtMacrosInvalidPmtFileError(
                        f"`{ env.py_snippets_stem }.py` files cannot be used as macro argument: they can "
                        f"only be used for code snippets inclusion.\n{ env.log() }"
                    )

        runner_file_and_extractor = ExtractorClass._get_file_extractor_for(
            env, rel_path, runner_file=runner_file,
        )
        return runner_file_and_extractor





#--------------------------------------------------------------------------------------






@dataclass(eq=False)
class SqlExtractor(SingleFileExtractorWithRems, FileExtractor, terminal=True):

    ARG_NAME:         ClassVar[str] = "sql_name"
    EXTENSION:        ClassVar[str] = ".sql"
    LEADING_HEADER:   ClassVar[str] =r"--[\t -]*"
    TRAILING_HEADER:  ClassVar[str] =r"[\t -]*--"
    INCLUSION_HEADER: ClassVar[str] = "--"






#--------------------------------------------------------------------------------------






@dataclass(eq=False)
class PythonExtractor(FileExtractor, terminal=True):

    ARG_NAME:         ClassVar[str] = "py_name"
    EXTENSION:        ClassVar[str] = ".py"
    LEADING_HEADER:   ClassVar[str] =r"#[\t ]*-+[\t ]*"
    TRAILING_HEADER:  ClassVar[str] =r"[\t ]*-+[\t ]*#"
    INCLUSION_HEADER: ClassVar[str] = "##"

    def iter_on_files(self):
        return (
            self.exo_file,
            self.rem_rel_path,
            self.vis_rem_rel_path,
            self.corr_rel_path,
            self.test_rel_path,
        )

    def extract_non_pmt_file(self, script_content:str):
        """
        "Old fashion way" extractions, with:
            - user code + public tests (+ possibly HDR) in the base script file (optional)
            - secret tests in "{script}_test.py" (optional)
            - Correction in "{script}_corr.py" (optional, but secret tests have to exist)
            - Remarks in "{script}_REM.md" (optional, but secret tests have to exist)

        (Bypass the super call)
        """
        log_exo = self.exo_file and Path(self.exo_file).relative_to(CWD)

        self.env.outdated_PM_files.append(
            (log_exo, self.env.file_location())
        )

        if script_content.startswith('#MAX'):
            # SOFT DEPRECATED (kept in case the user set the logger to `warn` instead of `error`)
            # If something about MAX in the file, it has precedence:
            self.env.warn_unmaintained(
                partial_msg = "Setting IDE MAX value through the file is deprecated. Move this "
                             f"to the IDE macro argument.\nFile: { log_exo }"
            )
            script = script_content
            first_line, script = script.split("\n", 1) if "\n" in script else (script,'')
            script_content = script.strip()
            self.file_max_attempts = first_line.split("=")[1].strip()

        sections = (
            ScriptData.env,
            ScriptData.code,
            ScriptData.tests,
            ScriptData.secrets,
            ScriptData.corr,
            ScriptData.REM,
            ScriptData.VIS_REM,
        )
        contents = (
            *self.env.get_hdr_and_public_contents_from(script_content, apply_strip=False),
            *map(self.get_file_content_or_empty_string, SiblingFile.VALUES)
        )
        self._assign_old_fashion_sections(zip(sections, contents))






@dataclass(eq=False)
class PythonSnippetsExtractor(SingleFileExtractor, PythonExtractor):

    def extract_files_content(self):
        script_content = read_file(self.exo_file) if self.exo_file else ""
        self.extract_monolithic_pmt_file(script_content)

    def validate_section(self, section:str, *, required=False):
        if section not in self.contents:
            self._raise_invalid_section(section)

    def check_potential_invalid_pmt_headers(
        self,
        script_content: str,
        headers: List[Tuple[str,str]],
        headers_and_matches: List[Tuple[str,str]],
    ):
        pass
