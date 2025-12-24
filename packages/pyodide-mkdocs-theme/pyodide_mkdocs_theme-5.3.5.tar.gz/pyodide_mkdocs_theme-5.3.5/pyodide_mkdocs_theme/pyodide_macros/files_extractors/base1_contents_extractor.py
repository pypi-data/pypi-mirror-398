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
"""
OUTDATED:   This is the orignal logic for python files.
            The current one sis a generalized version of this.

With `py_name` being denoted {X} and {F} being the stem of the current .md source file,
the extracted files may be:

    1.  {X}.py
        {X}_REM.md
        {X}_VIS_REM.md
        Where the py file contains all the needed python code/sections, separated by the
        pyodide python tokens: `# --- PMT:{kind} --- #`

    2.  {X}.py
        {X}_text.py
        {X}_corr.py
        {X}_REM.md
        {X}_VIS_REM.md

    3.  scripts/{F}/{X}.py
        scripts/{F}/{X}_REM.md
        scripts/{F}/{X}_VIS_REM.md
        Where the py file contains all the needed python code/sections, separated by the
        pyodide python tokens: `# --- PMT:{kind} --- #`

    4.  scripts/{F}/{X}.py
        scripts/{F}/{X}_test.py
        scripts/{F}/{X}_corr.py
        scripts/{F}/{X}_REM.md
        scripts/{F}/{X}_VIS_REM.md

The order gives the precedence. Way "1" is excluding the others (except for the REM file)
"""


import re
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Iterable, List, Optional, Set, Tuple, Union, DefaultDict


from ..exceptions import (
    PmtMacrosInvalidArgumentError,
    PmtMacrosInvalidPmtFileError,
    PmtMacrosInvalidSectionError,
    PmtMultiRemSourcesError,
    PmtTabulationError,
)
from ..tools_and_constants import ScriptData, SiblingFile
from ..parsing import items_comma_joiner
from ..paths_utils import read_file
from .base0_extractors import BaseExtractorWithCache


CWD = Path.cwd()




















@dataclass(eq=False)
class BasePmtSectionsTools(BaseExtractorWithCache):
    """
    Various definitions and methods to handle sections data, and the tokenization.
    """


    contents: Dict[str, str] = field(default_factory=dict)
    """
    Dict[section_name, section_content].

    This stores the original content of each section of the source file (without any modification
    aside from stripping). WARNING: may contain extra sections!
    """

    #Sections content access through getters (legacy)
    # vvvvvvvvv
    # GENERATED
    @property
    def env_content(self): return self.contents["env"] if "env" in self.contents else ""
    @env_content.setter
    def env_content(self, s:str): self.contents["env"] = s
    @property
    def env_term_content(self): return self.contents["env_term"] if "env_term" in self.contents else ""
    @env_term_content.setter
    def env_term_content(self, s:str): self.contents["env_term"] = s
    @property
    def code_content(self): return self.contents["code"] if "code" in self.contents else ""
    @code_content.setter
    def code_content(self, s:str): self.contents["code"] = s
    @property
    def corr_content(self): return self.contents["corr"] if "corr" in self.contents else ""
    @corr_content.setter
    def corr_content(self, s:str): self.contents["corr"] = s
    @property
    def tests_content(self): return self.contents["tests"] if "tests" in self.contents else ""
    @tests_content.setter
    def tests_content(self, s:str): self.contents["tests"] = s
    @property
    def secrets_content(self): return self.contents["secrets"] if "secrets" in self.contents else ""
    @secrets_content.setter
    def secrets_content(self, s:str): self.contents["secrets"] = s
    @property
    def post_term_content(self): return self.contents["post_term"] if "post_term" in self.contents else ""
    @post_term_content.setter
    def post_term_content(self, s:str): self.contents["post_term"] = s
    @property
    def post_content(self): return self.contents["post"] if "post" in self.contents else ""
    @post_content.setter
    def post_content(self, s:str): self.contents["post"] = s
    @property
    def rem_content(self): return self.contents["REM"] if "REM" in self.contents else ""
    @rem_content.setter
    def rem_content(self, s:str): self.contents["REM"] = s
    @property
    def vis_rem_content(self): return self.contents["VIS_REM"] if "VIS_REM" in self.contents else ""
    @vis_rem_content.setter
    def vis_rem_content(self, s:str): self.contents["VIS_REM"] = s
    @property
    def has_env(self): return "env" in self.contents
    @property
    def has_env_term(self): return "env_term" in self.contents
    @property
    def has_code(self): return "code" in self.contents
    @property
    def has_corr(self): return "corr" in self.contents
    @property
    def has_tests(self): return "tests" in self.contents
    @property
    def has_secrets(self): return "secrets" in self.contents
    @property
    def has_post_term(self): return "post_term" in self.contents
    @property
    def has_post(self): return "post" in self.contents
    @property
    def has_rem(self): return "REM" in self.contents
    @property
    def has_vis_rem(self): return "VIS_REM" in self.contents
    # GENERATED
    # ^^^^^^^^^

    # Properties aliases for backward compatibility (not used anymore/legacy):
    public_tests = tests_content
    secret_tests = secrets_content
    user_content = code_content


    file_max_attempts: str = ""
    """ [SOFT DEPRECATED] """


    test_rel_path: Optional[Path] = None
    """ Relative path to the ..._test.py file. Always defined, even if the file doesn't exist. """

    corr_rel_path: Optional[Path] = None
    """ Relative path to the ..._corr.py file. Always defined, even if the file doesn't exist. """

    rem_rel_path: Optional[Path] = None
    """ Relative path to the ...REM.md file. Always defined, even if the file doesn't exist. """

    vis_rem_rel_path: Optional[Path] = None
    """ Relative path to the ..._VIS_REM.md file. Always defined, even if the file doesn't exist. """


    @property
    def corr_rems_bit_mask(self):
        """
        Bit mask giving the configuration for correction and/or remark data:
            - mask & 1 -> presence of correction
            - mask & 2 -> presence of REM(s).

        Note: As property because the data are not available yet for `CompositeFilesDataExtractor`
        instances.
        """
        return self.has_corr + (self.has_rem or self.has_vis_rem) * 2


    #------------------------------------------------------------------------------------------


    def __post_init__(self):
        super().__post_init__()

        if self.exo_file is not None:
            rel_base = Path(self.exo_file).relative_to(CWD)
            (
                self.test_rel_path,
                self.corr_rel_path,
                self.rem_rel_path,
                self.vis_rem_rel_path,
            )=(
                rel_base.with_name(f"{ rel_base.stem }{ ending }") for ending in SiblingFile.VALUES
            )


    def validate_section(self, section:str, *, required=False):
        not_allowed = section not in self.env.allowed_pmt_sections
        absent      = section not in self.contents
        if not_allowed or required and absent:
            self._raise_invalid_section(section)


    def _raise_invalid_section(self, section:Optional[str]):
        trace = self.get_inclusion_trace()
        raise PmtMacrosInvalidSectionError(
            f'Invalid PMT section name: {section!r}.\n{ trace }\n{ self.env.log() }'
        )


    def get_file_content_or_empty_string(self, tail:str=None, using:Optional[Path]=None):
        """
        Return the content of the given file, or empty string if the file doesn't exist.

        If @using is an actual Path, use this path instead of searching for the appropriated
        file on the disk.

        @throws: PmtMacrosInvalidPmtFileError if a file is found but it's empty.
        """
        content = ''
        path: Union[Path,None] = using or self.env.get_sibling_of_current_page(self.arg_name, tail=tail)

        if path and path.is_file():
            path = path.relative_to(CWD)

            # Also checks that the file exists and contains something:
            if not path.is_file():
                path = None
            else:
                content = read_file(path).strip()
                if not content:
                    raise PmtMacrosInvalidPmtFileError(f"{path} is an empty file and should be removed.")
        return content



    def get_sections(self, sections:Iterable[ScriptData], with_headers:bool):
        """
        Related to the macro `composed_xxx`: compose the needed content, possibly adding headers
        in-between the sections.
        Empty sections are always ignored.
        """
        sections: Set[ScriptData] = set(sections)

        if not sections.issubset(self.env.allowed_pmt_sections):
            raise PmtMacrosInvalidArgumentError(
                f"Unknown PMT section name(s):\n"
                f"  Invalid members: { ', '.join( sections - self.env.allowed_pmt_sections ) }\n" +
                f"  Valid members are: { ', '.join( self.env.allowed_pmt_sections_in_order ) }\n\n" +
                self.env.log()
            )

        template = ("# --- PMT:{0} --- #\n" if with_headers else "") + "{1}"
        contents = []
        has_rems = self.has_rem or self.has_vis_rem

        def push(section,content):
            contents.append( template.format(section, content) )

        for section in self.env.allowed_pmt_sections_in_order:

            if section == ScriptData.REM and has_rems:
                push(ScriptData.ignore, '"""')

            if section in sections and (content := self.get_section(section)):
                push(section, content)

            if section == ScriptData.VIS_REM and has_rems:
                push(ScriptData.ignore, '"""')

        return "\n\n".join(contents)
















@dataclass(eq=False)
class BasePmtSectionsExtractor(BasePmtSectionsTools):
    """
    Define the generic behaviors and properties for the most generic PMT contents:

    - The various sections and their content
    - Various observers
    - file text actual extraction routines
    - ...
    """

    SECTION_TOKEN: ClassVar[re.Pattern] = None
    """ Used to split the files content. Defined by children classes. """

    LEADING_HEADER: ClassVar[str] = None
    """ Leading element of the sections delimiter token. Defined by children classes. """

    TRAILING_HEADER: ClassVar[str] = None
    """ Trailing element of the sections delimiter token. Defined by children classes. """


    @classmethod
    def build_sections_pattern(cls):
        pattern = rf'^({ cls.LEADING_HEADER }(?:PMT|PYODIDE)[\t ]*:[\t ]*\w+{ cls.TRAILING_HEADER }[\t ]*)$'
        return re.compile(pattern, flags=re.MULTILINE)


    #-------------------------------------------------------------------------------------


    def extract_files_content(self):
        """
        Main file extraction routine.
        """
        script_content = read_file(self.exo_file) if self.exo_file  else ""

        # Remove any old content, to allow spotting double sources error (even on re-serve,
        # avoiding false positives):
        self.contents.pop(ScriptData.REM, None)
        self.contents.pop(ScriptData.VIS_REM, None)

        if script_content:
            is_pmt_file = self.env.pmt_sections_pattern.search(script_content)
            if is_pmt_file:
                self.extract_monolithic_pmt_file(script_content)
            else:
                self.extract_non_pmt_file(script_content)

        # Check that no tab chars are used in the REMs contents (may mess up md rendering):
        for section in (ScriptData.REM, ScriptData.VIS_REM):
            if section not in self.contents:
                continue

            rem: str = self.contents[section]
            if '\t' not in rem:
                continue
            elif self.env.tab_to_spaces > -1:
                rem = rem.replace('\t', ' '*self.env.tab_to_spaces)
                self.contents[section] = rem
            else:
                raise PmtTabulationError(
                    "Found a tabulation character in a rem or vis_rem content. They should be "
                    f"replaced with spaces.{ self.env.log() }"
                )


    #-------------------------------------------------------------------------------------


    @staticmethod
    def get_section_name(header:str):
        """ Extract the section name of a PMT/PYODIDE header """
        return header.strip(' #-').split(':')[-1].strip()


    @staticmethod
    def strip_section(content:str):
        """
        Strip leading and trailing line feeds from a section content to remove empty lines, but not
        the indentation.
        NOTE: starting from PMT 5.0, DO NOT just "...".strip(), in case someone starts to concatenate
        partial codes already containing indented code.
        """
        return content.strip('\n')



    #--------------------------------------------------------------------------
    #                    MONOLITHIC (single PMT file) WAY
    #--------------------------------------------------------------------------


    def extract_monolithic_pmt_file(self, script_content:str):
        """
        Generic sections extraction logic, for a unique file containing PMT sections.
        Works with any kind of file.
        """
        sections_and_contents = self._analyze_single_file_content(script_content)

        # Valid sections registrations:
        for section,content in sections_and_contents:
            section_name = self.get_section_name(section)
            if section_name == ScriptData.ignore:
                continue
            self.contents[section_name] = self.strip_section(content)


        # Extract REMs checking that only one source of data is used:
        rems_siblings: List[Tuple[str,str]] = [
            (ScriptData.REM,     SiblingFile.rem),
            (ScriptData.VIS_REM, SiblingFile.vis_rem),
        ]
        for section,sibling in rems_siblings:
            existent = section in self.contents
            content  = self.get_file_content_or_empty_string(sibling)
            if existent and content:
                prop_path = section.lower() + '_rel_path'
                raise PmtMultiRemSourcesError(
                    f"Found both sources for { section } content:\n"
                    f"   - File: { getattr(self, prop_path) }\n"
                    f"   - `# --- PMT:{ section } --- #` section in { self.exo_file }."
                )
            elif content:
                self.contents[section] = self.strip_section(content)



    def _analyze_single_file_content(self, script_content:str):
        """
        Validate the file content against PMT normal "single file" structure and return an list
        of tuples (section_name, section_content).
        Only non empty and allowed PMT sections are extracted.

        @throws `PmtMacrosInvalidPmtFileError` if:

        - Missing a PMT header at the beginning of the file.
        - Wrong PMT headers "repartition" (empty section, for example).
        - Duplicated section names (unless `ignore`).
        - A suspicious/potential PMT header is found somewhere in the file but has not been
        identified as such.
        """

        # WARNING: at this point chunks MUST NOT be stripped yet, because headers and contents need
        # two different logics (PMT 5.0+ -> to allow concatenation of already indented codes):
        chunks  = self.SECTION_TOKEN.split(script_content)
        chunks  = [*filter(lambda s:bool(s.strip()), chunks)]   # remove sections with only spaces
        pairs   = [*zip(*[iter(chunks)]*2)]
        tic_toc = [ bool(self.SECTION_TOKEN.match(header.strip())) for header,_ in pairs ]
                    # Strip the header because of the condition bellow: `not tic_toc[0]`

        # File structure validations:
        headers_and_matches = [
            ( chunk, self.get_section_name(chunk) )
                for chunk in map(str.strip,chunks) if self.SECTION_TOKEN.match((chunk))
        ]
        headers = [ section for _,section in headers_and_matches]

        self.check_potential_invalid_pmt_headers(script_content, headers, headers_and_matches)

        if tic_toc and not tic_toc[0]:
            raise PmtMacrosInvalidPmtFileError(
                f"Invalid file structure for { self.exo_file }: no section header at the beginning of the file."
            )

        odds_sections = len(chunks) & 1
        wrong_tic_toc = len(headers) != sum(tic_toc)

        if odds_sections or wrong_tic_toc:
            raise PmtMacrosInvalidPmtFileError(
                f"Invalid file structure for { self.exo_file }: no empty sections allowed."
            )

        without_ignores_headers = [ h for h in headers if h != ScriptData.ignore ]
        headers_counter = Counter(without_ignores_headers)
        duplicates = sorted(name for name,n in headers_counter.items() if n>1)

        if duplicates:
            duplicates = items_comma_joiner(duplicates)
            raise PmtMacrosInvalidPmtFileError(
                f"Invalid file structure for { self.exo_file }: Duplicate sections are not "
                f"allowed (except for the `ignore` section). Found several { duplicates }."
            )

        return pairs


    def check_potential_invalid_pmt_headers(
        self,
        script_content: str,
        headers: List[Tuple[str,str]],
        headers_and_matches: List[Tuple[str,str]],
    ):
        """
        Check that some misformed PMT headers are not present in the file.

        @throws `PmtMacrosInvalidPmtFileError` if searching for the "PMT:{section}" does find a different
        number of matches than the normal header tokenizer.
        """
        header_pattern = self.env.pmt_sections_pattern
        potential_sections = [ (m[0],m[1]) for m in header_pattern.finditer(script_content)]

        if(len(potential_sections) != len(headers)):

            wrong = [
                "\n\t"+token for token,header in potential_sections if header not in headers
            ]+[
                "\n\t"+section for section,header in headers_and_matches if not header_pattern.search(section)
            ]
            valid_names = "\n\t".join(self.env.allowed_pmt_sections_in_order)

            raise PmtMacrosInvalidPmtFileError(
                f"Potential mistake in { self.exo_file }.\n\nThe following string(s) could match PMT "
                 "tokens, but weren't identified as such. Please check there are no formatting "
                 f"mistakes:{ ''.join(wrong) }\n\nA valid section token should match this pattern: "
                 f"{ self.SECTION_TOKEN.pattern !r}\n\nAllowed section names are:\n\t{ valid_names }"
            )


    #--------------------------------------------------------------------------
    #                            OLD FASHION WAY
    #--------------------------------------------------------------------------


    def extract_non_pmt_file(self, script_content:str):
        """
        Extraction of a bare file, supposedly containing only one section (implicitly / consider
        it's a `code` section).
        """
        log_exo = self.exo_file and Path(self.exo_file).relative_to(CWD)
        self.env.outdated_PM_files.append( (log_exo, self.env.file_location()) )

        sections_and_contents = (
            (ScriptData.code,     script_content),
            (ScriptData.REM,      self.get_file_content_or_empty_string(SiblingFile.rem)),
            (ScriptData.VIS_REM,  self.get_file_content_or_empty_string(SiblingFile.vis_rem)),
        )
        self._assign_old_fashion_sections(sections_and_contents)


    def _assign_old_fashion_sections(self, sections_and_contents:Iterable[Tuple[ScriptData,str]]):
        for section,content in sections_and_contents:
            if content:
                stripped = self.strip_section(content)
                self.contents[section] = stripped
