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
# pylint: disable=multiple-statements, no-member



from typing import ClassVar, Dict, List, Literal, Optional, Set, Tuple, Union, TYPE_CHECKING
from dataclasses import dataclass, field, fields

from ..exceptions import PmtMacrosInvalidArgumentError
from ..messages.fr_lang import LangFr


if TYPE_CHECKING:
    from pyodide_mkdocs_theme.pyodide_macros import PyodideMacrosPlugin





@dataclass
class Case:
    """
    Represent a test case for an IDE TEST argument (or profile).

    Case objects only holds the configuration for a test, not the data related to the IDE it is
    run for. These are held by IDEs themselves, meaning they will have to be extracted from each
    page, extracting the PAGES_IDES_CONFIG compressed code directly from the html page.

    Case object will be transferred to the test_ides page as JSON objects, following these specs:
    - None values are never exported.
    - Falsy values (JS-wise) on the outer Case object are not exported (resulting in undefined in JS)
    - Falsy values on subcases ARE exported because, if defined, they override a value on the parent
    - Fields that are never used in JS are not exported: see `self.NOT_DUMPED`.
    - subcases arrays/tuples are always exported even if empty, to simplify the JS implementation.
    """

    NOT_DUMPED: ClassVar[Set[str]] = {
        'description', 'title', 'all_in_std', 'none_in_std'
    }
    """
    Properties not exported to JS.
    """

    DESC_SKIPPED: ClassVar[Tuple[str]] = {
        'subcases', 'skip', 'description', 'title', 'std_capture_regex', 'not_std_capture_regex',
    }
    """
    Not shown in the automatic descriptions.
    """


    DESC_SHORTEN: ClassVar[Dict[str,str]] = {
        'decrease_attempts_on_user_code_failure': 'decrease_on_fail',
        'deactivate_stdout_for_secrets':          'secrets_std_out',
        'show_only_assertion_errors_for_secrets': 'secrets_assert_only',
    }
    """
    Automatic descriptions formatting.
    """


    # Globals for string definitions (public interface)
    DEFAULT: ClassVar['Case'] = None     # Defined after class declaration
    SKIP:    ClassVar['Case'] = None     # Defined after class declaration
    HUMAN:   ClassVar['Case'] = None     # Defined after class declaration
    FAIL:    ClassVar['Case'] = None     # Defined after class declaration
    NO_CLEAR:ClassVar['Case'] = None     # Defined after class declaration
    CODE:    ClassVar['Case'] = None     # Defined after class declaration
    CORR:    ClassVar['Case'] = None     # Defined after class declaration


    # Private interface
    REVEAL_SUCCESS:             ClassVar['Case'] = None
    REVEAL_FAIL:                ClassVar['Case'] = None
    ERROR_IN_POST_REVEAL:       ClassVar['Case'] = None
    ERROR_NO_REVEAL:            ClassVar['Case'] = None
    SUCCESS_AFTER_REVEAL:       ClassVar['Case'] = None
    DELAYED_NO_REVEAL:          ClassVar['Case'] = None
    SUCCESS_NOTHING_TO_REVEAL:  ClassVar['Case'] = None


    #--------------------------------------------------------------------------


    human: Optional[bool] = None
    """
    If True, this IDE is not tested by default, but it can be selected with the human button (to
    use for tests that require human actions, like up-/downloads).
    """

    skip: Optional[bool] = None
    """
    Don't test this IDE
    """

    fail: Optional[bool] = None
    """
    This IDE has to raise something during the test
    """

    code: Optional[bool] = None
    """
    Run the `code` section instead of the `corr` one.
    """

    no_clear: Optional[bool] = None
    """
    Don't clear the scope before doing this test (NOTE: this would become useless if the tests
    were not run in order).
    """

    term_cmd: Optional[str] = None
    """
    One command to execute through the terminal. If given, corr/code sections to test are ignored.
    """

    description: Optional[str] = None
    """
    Quick description of the test (optional).
    """



    #-------------------------------------------------------------------------
    # Private interface:

    all_in_std: Optional[List[str]] = None
    """
    If given, automatically build a regex with all the element for `std_capture_regex`.

    !!! warn ""
        * This will apply on content already formatted by jQuery.terminal output, so terminal
        colors may mess up the patterns.
        * The order of the string to match matters: all string have to be matched in order.
    """

    none_in_std: Optional[List[str]] = None
    """
    If given, automatically build a regex with all the element for `not_std_capture_regex`.

    !!! warn ""
        * This will apply on content already formatted by jQuery.terminal output, so terminal
        colors may mess up the patterns.
        * The order of the string to match DOES NOT matter: they can be given in any order.
    """

    in_error_msg: Optional[str] = None
    """
    String that should be found in the error message (test failed if no error message).
    """

    not_in_error_msg: Optional[str] = None
    """
    String that should NOT be found in the error message (success if no error message).
    """




    auto_run: Optional[bool] = None
    """
    Allow to test AUTO_RUN arguments.

    If True, will run the code using this.runner, or runnerTerm if a term_cmd is defined.
    """

    clear_libs: Optional[List[str]] = None
    """
    List of names of libs to remove before a test. This will automatically remove the zip files
    in the WASM file system, and remove the entry from `sys.modules` so that the python_lib can
    be loaded and trigger the import message again in the terminal.
    """

    deactivate_stdout_for_secrets:          Optional[bool] = None
    """ Override the current value for the source page, if given. """

    decrease_attempts_on_user_code_failure: Optional[str]  = None
    """ Override the current value for the source page, if given. """

    run_play: Optional[bool] = None
    """
    Runs the public tests only. Here, it's still possible to run either the code or the
    corr section, along with the tests section.
    """

    run_corr: Optional[bool] = None
    """
    Runs the ValidationCorr
    """

    set_max_and_hide: Optional[int] = None
    """
    Allow to change the number of attempts left before the test, and reset the state of any
    previously revealed stuff. Use 1000 to get infinite number of attempts.
    """

    show_only_assertion_errors_for_secrets: Optional[bool] = None
    """ Override the current value for the source page, if given. """





    assertions: Optional[str] = None
    """
    Space separated strings of boolsy `IdeRunner` properties to check at the end of the test.

    * Prefix with '!' to check for falsy values.
    * Identifiers can be in camelCase or snake_case, so any JS property can be tested.
    * If a property returns undefined, the test will be considered failed.

    Available properties (non exhaustive):

    - `allowPrint`
    - `attemptsLeft`
    - `autoLogAssert`
    - `autoRun`
    - `corrContent`
    - `corrRemsMask`
    - `cutFeedback`
    - `deactivateStdoutForSecrets`
    - `decreaseAttemptsOnUserCodeFailure`
    - `envContent`
    - `envTermContent`
    - `excluded`
    - `excludedKws`
    - `excludedMethods`
    - `export`
    - `hasCheckBtn`
    - `hasCorrBtn`
    - `hasCounter`
    - `hasRevealBtn`
    - `hasTerminal`
    - `hasTerminal`
    - `hasTerminal`
    - `isDelayedRevelation`
    - `isIde`
    - `isIde`
    - `isInSequentialRun`
    - `isInSplit`
    - `isPyBtn`
    - `isPyBtn`
    - `isRunner`
    - `isStarredGroup`
    - `isTerminal`
    - `isTerminal`
    - `isTerminal`
    - `isVert`
    - `maxIdeLines`
    - `minIdeLines`
    - `orderInGroup`
    - `postContent`
    - `postTermContent`
    - `prefillTerm`
    - `profile`
    - `publicTests`
    - `pyName`
    - `pypiWhite`
    - `pythonLibs`
    - `recLimit`
    - `removeAssertionsStacktrace`
    - `revealCorrRems`
    - `runGroup`
    - `secretTests`
    - `seqPlay`
    - `seqRun`
    - `showOnlyAssertionErrorsForSecrets`
    - `splitScreenActivated`
    - `srcHash`
    - `stdKey`
    - `stdoutCutOff`
    - `twoCols`
    - `userContent`
    - `whiteList`
    """
    # GENERATED doc
    # ^^^^^^^^^

    delta_attempts: Optional[Literal[0,-1]] = None
    """
    `#!py 0` or `#!py -1`, if used: expected variation of number of attempts at the end or the test.
    """



    subcases: List['Case'] = field(default_factory=list)
    """
    List of Case objects, defining a group of tests.

    ```python
    Case(description="nom du groupe de tests", subcases=[
        Case(title='cas 2', ...),
        Case(title='cas 1', ...),
        ...
    ])
    ```
    """

    title: Optional[str] = None
    """
    String prepended to the automatic description when no description value given
    """


    #---------------------------------------------------------------------

    # std_capture_regex: Optional[str] = None
    # """ INTERNAL ONLY: DON'T USE THAT AS ARGUMENT """
    # not_std_capture_regex: Optional[str] = None
    # """ INTERNAL ONLY: DON'T USE THAT AS ARGUMENT """

    def __post_init__(self):

        if self.subcases:
            self.subcases = [*map(self.auto_convert_str_to_case, self.subcases)]


    def times(self, n:int, with_:Dict[Union[int,Tuple[int]],'Case']=None):
        """
        Creates `n` subcases for the current Case object. This is useful for tests involving
        `py_libs.auto_N(...)` and `py_libs.do_it(...)`.

        If the `with_` dict is given, the subcases at the given keys (either int or tuple of
        ints, meaning "n-th" subcase) will be replaced with the `Case` corresponding value.
        """
        if self.subcases:
            raise PmtMacrosInvalidArgumentError(
                "Cannot use `Case.times(n)` method if the instance already has a `subcases` array."
            )
        self.subcases = [ Case(description=f"Run {i+1}") for i in range(n) ]
        if with_:
            for ns,case in with_.items():
                if isinstance(ns,int):
                    ns = (ns,)
                for n in ns:
                    self.subcases[n-1] = case
        return self


    def with_(self, **kwargs):
        """
        Build a new Case instance based on the current one, updating all the properties with the
        one of the kwargs.
        """
        # Always keep falsy values, toi be sure properties will be properly defined/overridden
        # (also important with .times(...)).
        kw = {**self._to_dict(keep_falsy=True), **kwargs}

        # Special case to add dedicated descriptions to the CONSTANTS CASES (see bottom of this file)
        if self.description is not None and kwargs and 'description' not in kwargs:
            kw['description'] += ' | '+', '.join( self.format_item(k,v) for k,v in kwargs.items() )

        return Case(**kw)



    @classmethod
    def auto_convert_str_to_case(cls, case: Union[str,'Case']) -> 'Case':
        """
        Convert a string to the related Case instance, or just return the instance.
        """
        if isinstance(case, Case):
            return case
        if not isinstance(case, str):
            raise PmtMacrosInvalidArgumentError(
                f"TEST argument should be a string or a Case instance, but was: {case!r}"
            )
        out = cls.DEFAULT if not case else getattr(cls, case.upper())
        return out.with_()      # Always return a copy!



    @classmethod
    def format_item(cls, k, v):
        """
        Used to make some automatic descriptions shorter...
        """
        return f"{ cls.DESC_SHORTEN.get(k,k) }={ repr(v) }"



    def _to_dict(self, keep_falsy=False, skipped_props=()):
        """
        Convert to a dict, without the properties whose the value is None.
        """
        dumped = {
            f.name: v  for f in fields(self)
                        if f.name not in skipped_props          # Useful in the JS layer of the tests...
                        and (                                   # ...and:
                            (v:=getattr(self, f.name))          #   Always export truthy
                            or f.name=="subcases"               #   (only to ease the JS implementation)
                            or v is not None and (              #   Export falsy only if...
                                keep_falsy or                   #       - Asked for (means depth>0 aka a subcase)
                                f.name == 'no_clear'            #       - Special case, because may be automatically set in the JS later
                            )
                        )
        }
        return dumped


    def as_dict(self, depth:int=0):
        """
        Convert recursively to a dict, removing falsy values.
        """
        dct = self._to_dict(keep_falsy=depth>0, skipped_props=self.NOT_DUMPED)

        if self.all_in_std is not None:
            dct['std_capture_regex'] = r'.*?'.join(self.all_in_std)
        if self.none_in_std is not None:
            dct['not_std_capture_regex'] = r'|'.join(self.none_in_std)

        if self.subcases:
            if depth:
                raise PmtMacrosInvalidArgumentError(
                    f"Case objects in a Case.subcases list cannot contain subcases themselves."
                )
            dct['subcases'] = [ case.as_dict(depth+1) for case in self.subcases ]

        return dct



    def get_description(self, is_root:bool):
        if self.description is not None:
            return self.description

        description = ', '.join(
            self.format_item(k,v)
                for k,v in self._to_dict().items()
                if k not in self.DESC_SKIPPED           # Don't show irrelevant info
                    and (k!='code' or is_root)          # Useless if not at top level: already known
        )
        if self.title:
            description = f"{ self.title }: { description }"
        return description






Case.SKIP     = Case(skip=True)
Case.FAIL     = Case(fail=True)
Case.CODE     = Case(code=True)
Case.CORR     = Case()                  # Default case before PMT 5.0
Case.HUMAN    = Case(human=True)
Case.NO_CLEAR = Case(no_clear=True)

Case.DEFAULT = Case(no_clear=False, description="", subcases=[
    Case(description="corr vs validation (succès)"),
    Case(description="code vs validation (échec)", code=True, fail=True),
    # Case(description="`code` vs `tests` (échec)", code=True, fail=True, run_play=True),
])



Case.REVEAL_SUCCESS = Case(
    description = "Success reveal with: bravo, passé tous les tests, pensez à lire",
    no_clear = True,
    fail = False,
    run_play = False,
    delta_attempts = 0,
    assertions = "corrRemsMask hasCheckBtn reveal_corr_rems",
    all_in_std = [LangFr.success_head.msg, LangFr.success_head_extra.msg, LangFr.success_tail.msg],
    none_in_std = [LangFr.fail_head.msg],
)

Case.REVEAL_FAIL = Case(
    description = "Fail reveal with: Dommage! and none of the success messages",
    fail = True,
    no_clear = True,
    run_play = False,
    delta_attempts = -1,
    assertions = "corrRemsMask hasCheckBtn reveal_corr_rems",
    none_in_std = [LangFr.success_head.msg, LangFr.success_head_extra.msg, LangFr.success_tail.msg],
    all_in_std = [LangFr.fail_head.msg],
)

Case.ERROR_IN_POST_REVEAL = Case(
    description = "Assertion in post is a success",
    fail = True,
    no_clear = True,
    run_play = False,
    delta_attempts = 0,
    assertions = "corrRemsMask hasCheckBtn reveal_corr_rems",
    none_in_std = [],
    all_in_std = [
        LangFr.success_head.msg, LangFr.success_head_extra.msg,
        LangFr.success_tail.msg,
        'Error:'
    ],
)

Case.ERROR_NO_REVEAL = Case(
    description = "Error without revelation",
    fail = True,
    no_clear = True,
    run_play = False,
    delta_attempts = -1,
    assertions = "corrRemsMask hasCheckBtn !reveal_corr_rems",
    all_in_std = ['Error:'],
    none_in_std = [ LangFr.fail_head.msg,
                    LangFr.success_head.msg, LangFr.success_head_extra.msg, LangFr.success_tail.msg],
)

Case.SUCCESS_AFTER_REVEAL = Case(
    description = "SUCCESS_AFTER_REVEAL",
    no_clear = True,
    fail = False,
    run_play = False,
    delta_attempts = 0,
    assertions = "hasCheckBtn !reveal_corr_rems",
    none_in_std = [LangFr.success_head.msg, LangFr.success_head_extra.msg, LangFr.fail_head.msg, LangFr.success_tail.msg],
)

Case.SUCCESS_NOTHING_TO_REVEAL = Case.SUCCESS_AFTER_REVEAL.with_(
    none_in_std = [LangFr.fail_head.msg, LangFr.success_tail.msg],
    all_in_std  = [LangFr.success_head.msg, LangFr.success_head_extra.msg],
)

Case.DELAYED_NO_REVEAL = Case(
    description = "DELAYED_NO_REVEAL",
    no_clear = False,
    fail = False,
    run_play = False,
    delta_attempts = -1,
    assertions = "hasCheckBtn !reveal_corr_rems",
    none_in_std = [LangFr.success_head.msg, LangFr.success_head_extra.msg, LangFr.fail_head.msg, LangFr.success_tail.msg],
)
