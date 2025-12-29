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
# Extractor general contracts/logic:
------------------------------------


Represent all the files associated to a runner (IDE, terminal, ...), holding the logic/tools
to build the various sections contents.

Context/Contracts/Goals:

* An Extractor is linked to a single PMT file, with its potential "direct" dependencies
(aka REMs, or tests/corr files par for the PM source project's format).

* The PMT file can actually not exist at all! (in that case, exo_py is None)

* A PMT file, if it exists, contains sections, delimited by tokens in the form:
        `{something} (PMT|PYODIDE):{section} {something}`
`something` being different depending on what is the file to extract (python, sql, ...).
.
* An Extractor instance is cached based on the absolute/resolved path to the main file
(self.exo_py).

* The cache is automatically refreshed when a local file has been modified (based on the
stats of the file). NOTE: this update is done at the on_config step, to avoid checking on
each extractor use/call.

* The contents of the files are stored in the instance, avoiding multiple HDD reads operations.

* Inclusions instructions are gathered after the file content has been read, WITHOUT recursively
triggering extraction of successors: these will be resolved on demand, when building contents.
NOTE: this is to allow .snippets.py file containing multiple sections, some of them not being
used in the "parent" file. These .snippets.py files often using [py] redirections, forcing the
resolution of the children might cause crashes if some sections of the .snippets.py file would
require specific content in the parent file while they aren't actually needed for this file.

* The final/actual contents are never stored in the object: sections (inclusions) are rebuilt
on the fly each time they are needed (relying on the fact reading a file is longer than string
concatenations, and that the simplification this allows in the implementation compensate for
the extra computation time).
"""
# pylint: disable=multiple-statements, missing-function-docstring


from pathlib import Path
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Iterable, Optional, Set, Tuple, TYPE_CHECKING, Type



from ..exceptions import PmtMacrosInvalidPmtFileError

if TYPE_CHECKING:
    from pyodide_mkdocs_theme.pyodide_macros import PyodideMacrosPlugin
    from ..plugin.maestro_macros import MaestroMacros
    from .base3_generic_extractors import GenericExtractor


CWD = Path.cwd()















@dataclass
class BaseFilesExtractor:
    """
    Hold the basic file management logic and the basic properties, as well as the general
    interface and contracts.

    - source file and `arg_name` argument
    - cache management
    - file content extraction generic triggers
    - hash and/or equality definitions
    - abstract methods that must be implemented at some point in the hierarchy
    """

    env: 'MaestroMacros'

    arg_name: str
    """
    The {exo}.py string leading to the targeted file (which may not actually exist).
    """

    runner_file: Optional[Path] = None
    """
    Path to the master main file (if any), as built when searching for sibling files.
    This is NOT a resolved path and can be used by runners to build their html id hash.
    """

    exo_file: Optional[Path] = None
    """
    Path to the master main file (if any).
    Also used as key cache to retrieve an Extractor instance.

    WARNING: This path is absolute AND normalized, while an exo_py for an IDE actually needs the
             absolute UNnormalized path when generating its html id (for backward compatibility,
             when checking their uniqueness).
    """

    docs_file: Optional[Path] = None
    """
    Same as self.exo_file, but relative to the CWD (logging and error messages purpose).
    """

    in_pages: Set[str] = field(default_factory=set)
    """

    """

    # ---------------------------------------------------------------------------------

    ARG_NAME: ClassVar[str] = None
    """
    Marco argument name used to define self.arg_name (aka py_name for IDEs, for example).
    Used to build dedicated error messages.
    """


    def __post_init__(self):

        if self.runner_file:
            self.exo_file  = Path(self.runner_file).resolve()
            self.docs_file = Path(self.exo_file).relative_to(CWD)
            md_uri = self.env.page.file.src_uri
            self.in_pages.add(md_uri)

        if self.arg_name and not self.runner_file:
            raise PmtMacrosInvalidPmtFileError(
                f"No file could be found for { self.ARG_NAME }='{ self.arg_name }'."
                f"{ self.env.log() }"
            )


    def __hash__(self):
        return hash(self.exo_file)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.exo_file == other.exo_file

    #------------------------------------------------------------------------------


    @classmethod
    def _get_file_extractor_for(
        cls, env:'PyodideMacrosPlugin', rel_path:str, *, runner_file:Optional[Path]=None, allow_snippets_py=False
    ) -> Tuple[Path, 'GenericExtractor'] :
        """
        Build a fresh Extractor object of extract the one coming from the class level cache.

        @rel_path:      The argument passed to the macro.
        @runner_file:   Path to the target file to extract. Allows to avoid auto-discovery step.
        @allow_snippets_py: Special flag to set tio True if there are some specific constraints
                        to spot when crating the top level object (inclusions-wise).

        @returns:       A tuple (UN-resolved Path to the target, Extractor instance).
                        The unresolved path cannot be archived in the instance/cache, because the
                        same file could be accessed from different places in the docs, while the
                        IdeManager will differentiate the resulting html id hashes based in this
                        unresolved path.
        """
        raise NotImplementedError()


    @classmethod
    def get_inclusion_trace(cls):
        """ Build the full path of inclusions resolutions up to the error point. """
        raise NotImplementedError()


    def extract_contents(self):
        """
        Extract the content of the current file (without resolving inclusions).
        """
        raise NotImplementedError()


    def extract_files_content(self):
        """
        Special method/hook to actual extract file contents from the HDD.
        (done this way so that the mtime_infos data are updated only once the extractions are
        finished and successful. This avoids marking a failure as correctly extracted).
        """
        raise NotImplementedError()


    def iter_on_files(self) -> Iterable[Optional[Path]]:
        """
        Iteration over the various files related to the current object, to determine when it is
        outdated or not, based on the file last modification time.
        This will return an iterable of the py principal file and its potential siblings (REMs,
        VIS_REMs, potentially {exo}_corr.py or {exo}_tests.py).

        This doesn't consider inclusion mechanics.
        """
        raise NotImplementedError()


    def get_section(self, section:str) -> str:
        """
        Extract the given section, verifying its name validity and resolving inclusions.
        If the section is an allowed PMT section but it has no content, return empty string.
        """
        raise NotImplementedError()















@dataclass(eq=False)
class BaseExtractorWithCache(BaseFilesExtractor):
    """ Isolated layer regrouping the cache logistic and instances creation. """


    EXTENSION: ClassVar[str] = None
    """
    Expected file extension of the target file (with the dot, as in Path.suffix).
    """

    _CACHED_EXTRACTORS: ClassVar[Dict[Path, 'GenericExtractor']] = {}
    """
    Class level cache of instances. This HAS to be overridden in one of the children classes
    in the hierarchy, allowing different caches in different branches, all using the same
    implementation.
    """

    _mtime_infos: Dict[Path, Optional[int]] = None



    @classmethod
    def _get_file_extractor_for(
        cls,
        env: 'PyodideMacrosPlugin',
        rel_path: str,
        *,
        runner_file: Optional[Path] = None,
        allow_snippets_py: bool = None,
    ) -> Tuple[Path, 'GenericExtractor'] :

        if not runner_file:
            runner_file = env.get_sibling_of_current_page(rel_path, tail=cls.EXTENSION)

        exo_file  = runner_file and Path(runner_file).resolve()
        extractor = cls._CACHED_EXTRACTORS.get(exo_file)

        if not extractor:
            extractor = cls(env, rel_path, runner_file=runner_file)
            cls._CACHED_EXTRACTORS[exo_file] = extractor
            extractor.extract_contents()
        elif not extractor.is_up_to_date():
            extractor.extract_contents()

        return runner_file, extractor


    def mark_up_to_date(self):
        """ Store the files timestamps to track the extractions needs. """
        self._mtime_infos = self._get_files_mtime_infos()


    def _get_files_mtime_infos(self):
        return {
            file: file.stat().st_mtime_ns if file and file.is_file() else None
            for file in self.iter_on_files()
        }

    def is_up_to_date(self):
        return self._mtime_infos == self._get_files_mtime_infos()
