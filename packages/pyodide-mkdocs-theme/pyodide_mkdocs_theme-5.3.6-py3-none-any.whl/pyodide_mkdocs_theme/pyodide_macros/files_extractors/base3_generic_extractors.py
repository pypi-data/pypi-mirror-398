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
from pathlib import Path
from typing import ClassVar, Dict

from ..exceptions import PmtInternalError
from .base2_inclusions import FileExtractorWithInclusions

CWD = Path.cwd()








@dataclass(eq=False)
class GenericExtractor(FileExtractorWithInclusions):
    """
    Intermediate "top base" class, enforcing the various contracts on "terminal" subclasses.
    """

    EXTENSION_TO_EXTRACTOR_CLASS: ClassVar[Dict[str,'GenericExtractor']] = {}

    def __init_subclass__(cls, terminal=False, **_):
        """
        Finalize the various class level variables on all the subclasses marked as `terminal=True`
        and register them in the ExtractorsPool, for later use.
        """
        if terminal:
            required = '''
                ARG_NAME
                EXTENSION
                LEADING_HEADER
                TRAILING_HEADER
                INCLUSION_HEADER
            '''.split()

            for prop in required:
                if getattr(cls, prop, None) is None:
                    raise PmtInternalError(f"{cls.__name__}.{prop} class level property is not defined.")

            cls.INCLUSION_PATTERN = cls.build_inclusions_pattern()
            cls.SECTION_TOKEN     = cls.build_sections_pattern()

            cls.EXTENSION_TO_EXTRACTOR_CLASS[cls.EXTENSION] = cls


    def extract_contents(self):
        super().extract_contents()
        self.mark_up_to_date()
            # AFTER all inclusions are analyzed (avoids marking the file as up to date if an
            # error occurs during the process).








@dataclass(eq=False)
class SingleFileExtractor(GenericExtractor):

    def iter_on_files(self):
        return (self.exo_file,)



@dataclass(eq=False)
class SingleFileExtractorWithRems(GenericExtractor):

    def iter_on_files(self):
        return (
            self.exo_file,
            self.rem_rel_path,
            self.vis_rem_rel_path,
        )
