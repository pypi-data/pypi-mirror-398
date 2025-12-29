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
from dataclasses import dataclass, field
import re
from textwrap import dedent
from typing import Any, Callable, ClassVar, Dict, Iterator, List, TYPE_CHECKING, NewType, Optional, Tuple, Type





from ..exceptions import PmtMacrosInvalidArgumentError
from .. import html_builder as Html
from ..tools_and_constants import HtmlClass, PageUrl, PmtPyMacrosName, PageInclusion, Prefix, Qcm, ScriptSection, ScriptData
from ..parsing import compress_LZW
from ..html_dependencies.deps_class import DepKind
from ..plugin_tools.test_cases import Case
from ..plugin_tools.macros_data import IdeToTest
from .ide_term_ide import CommonGeneratedIde
from .ide_ide import Ide


if TYPE_CHECKING:
    from ..plugin.pyodide_macros_plugin import PyodideMacrosPlugin



HtmlStr  = NewType('HtmlStr', str)
JsonDump = NewType('JsonDump', Dict[str,Any])


SECTIONS_BOXES_ORDER = (
    ScriptData.env,
    ScriptData.code,
    ScriptData.tests,
    ScriptData.secrets,
    ScriptData.post,

    ScriptData.env_term,
    ScriptData.corr,
    ScriptData.REM,
    ScriptData.VIS_REM,
    ScriptData.post_term,
)













@dataclass
class IdeTester(CommonGeneratedIde, Ide):

    MACRO_NAME: ClassVar[PmtPyMacrosName] = PmtPyMacrosName.IDE_tester

    ID_PREFIX: ClassVar[str] = Prefix.tester_

    DEPS_KIND: ClassVar[DepKind] = DepKind.ides_test

    nth_item:  ClassVar[str] = ""
    nth_style: ClassVar[str] = ""

    @property
    def has_check_btn(self):
        """ The IdeTester always has one... """
        return True

    @property
    def has_counter(self):
        """ The IdeTester always has one... """
        return True


    def register_ide_for_tests(self):
        """ IdeTester instances are never registered for testing... """


    def list_of_buttons(self):
        """ Keep only public tests, validations and restart. """
        btns    = super().list_of_buttons()
        restart = next(btn_html for btn_html in btns if "icons8-restart-64.png" in btn_html)
        return btns[:2] + [restart]


    def counter_txt_spans(self):
        """ No counter below the IDE, unless run in `_dev_mode`. """
        if self.env._dev_mode:                  # pylint: disable=protected-access
            return super().counter_txt_spans()
        return ''


    @classmethod
    def get_markdown(cls, use_mermaid:bool):
        """
        Build the code generating the IdeTester object. Insert the MERMAID logistic only if
        the `mkdocs.yml` holds the custom fences code configuration.
        """
        return dedent(f"""
            # Testing all IDEs in the documentation {'{'} data-search-exclude {'}'}

            <br>

            {'{{'} IDE_tester(MAX='+', MERMAID={ use_mermaid }, TERM_H=15) {'}}'}

        """)


    @classmethod
    def build_html_for_tester(
        cls,
        env:'PyodideMacrosPlugin',
        pages_with_ides: Dict[PageUrl, List[IdeToTest]],
    ) -> str :
        """
        Build all the html base elements holding the results/information for each IDE to test.
        """
        builder = TestsHtmlManager(env, cls)
        html = builder.build_html_for_tester(pages_with_ides)
        return html















@dataclass
class TestsHtmlManager:
    """
    Helper to build the html content for the tests page, centralizing global data on the way.

    * All tests are stored in CASES_DATA (list of conf objects)
    * The table is a 4xN css grid
    * Each cell is wrapped with a <div class="py_mk_test_element ...">
    * Each line has a "Play" button
    * Each play button holds data info:
        - data-conf-start and data-conf-end (exclusive): indices of the conf objects.
          Note that data-conf-end-1 is the index of the conf object of the current test!
        - data-i-row: index of the row in the table
      Play buttons for IDEs with sub-tests have additional values:
        - data-row-start: index of the first subtext row (in the table!)
        - data-row-end: index of the last subtest (excluded)
        - data-has-group: allow to quickly spot that this element has subtests.
    """

    CONF_TO_MERGE: ClassVar[Tuple[str,...]] = tuple('editor_id ide_link ide_name page_url rel_dir_url'.split())

    env: 'PyodideMacrosPlugin'
    ide_tester: Type[IdeTester]

    n_ides:  int = 0
    """ Number of IDEs. """
    n_ides_no_tests: int = 0
    """ Number of IDEs without tests (aka with subcases). """
    n_todo:  int = 0
    """ Number of tests to do (not skipped). """

    i_start_batch: int = 0
    """ Index of the row of the current IDE in the table. """
    i_row: int = -1
    """ Number of the current test/item (=index of the current row in the table). """

    ide_item: IdeToTest = None
    """ Current ide handled """
    nth_row_var: str = ''
    """ CSS var name for the current item/test (item "id") """
    nth_style: str = ''
    """ CSS style rule name for the current item/test (display) """

    with_load_buttons: bool=True
    """ Add the load buttons in hte interface or not. """

    cases_data: List[JsonDump] = field(default_factory=list)
    """
    List to store all the CASE_DATA items, to convert to JSON to pass to the JS layer.
    This is holding tree objects => length DOES NOT match the `rows_infos` list length.
    """

    rows_infos: List[JsonDump] = field(default_factory=list)
    """
    List of rows information: one element per table row, centralizing the initial data for each row:
        [i_conf_start:int, i_conf_end:int]

        * `i_conf_start` is always the row/index of the conf data for the holding IDE
        * `i_conf_end` is the index line where to stop the tests (upper bound exclusive)
        * Presence of subcases can be spotted using:   has_subcases = i_conf_start < i_conf_end-1

    Allows to pass the data through JS arrays (reduces the html amount to create).
    """

    css_rules: List= field(default_factory=list)
    """ Vars that are held by the outer div of the table. """


    def next_row(self):
        """ Update all internal states to build the next iem/row/test """
        self.i_row += 1
        self.nth_row_var = f'--item-{ self.i_row }'
        self.nth_style = f"display:var({ self.nth_row_var });"


    def grid_cell_div(self, element, id=None, kls=None,**kw):
        """
        Div factory, with automatic addition of dedicated html id and class.
        All these divs are the outer cells of the css grid, so they always hold common classes
        for the current row. Also add the default styling rule for that row.

        - If @id is not given, no html id. If it's given, build automatically a unique id
            looking like: "{ id }-{ self.ide_item.storage_id }"
        - @kls: additional classes to add to the element.
        """
        return Html.div(
            element,
            id    = id and f"{ id }-{ self.ide_item.storage_id }",
            kls   = f"{ HtmlClass.py_mk_test_element } { kls or '' }".rstrip(),
            style = self.nth_style,
            **kw
        )


    #--------------------------------------------------------------------------------


    def build_html_for_tester(
        self,
        pages_with_ides: Dict[PageUrl, List[IdeToTest]],
    ) -> HtmlStr :
        """
        Build all the html base elements holding the results/information for each IDE to test.
        """

        self.with_load_buttons = self.env.testing_include == PageInclusion.serve
        if self.env.testing_load_buttons is not None:
            self.with_load_buttons = self.env.testing_load_buttons

        table_rows = []
        for ides in pages_with_ides.values():
            for one_ide in ides:
                self.build_ide_items(one_ide, table_rows)

        div_table    = Html.div(''.join(table_rows), id=HtmlClass.py_mk_tests_results)
        js_data      = json.dumps(self.cases_data)
        js_data      = repr(compress_LZW(js_data, self.env))
        cases_script = f"<script>const CASES_DATA={ js_data }</script>"

        filters    = self.build_filters()
        controller = self.build_global_controller()

        inner = controller + filters + Html.div(div_table, id=HtmlClass.py_mk_tests_table)
        outer = Html.div(
            inner + cases_script,
            id = HtmlClass.py_mk_test_global_wrapper,
            kls = Qcm.multi,
            style = ';'.join(self.css_rules)
        )
        return outer


    #--------------------------------------------------------------------------------


    def build_ide_items(self, ide_item:IdeToTest, table_rows:List[HtmlStr]):

        self.n_ides += 1
        self.ide_item  = ide_item
        self.cases_data.append(ide_item.as_dict())
        self.next_row()

        i_row_ide = len(table_rows)
        self.i_start_batch = self.i_row

        # ide_var = self.nth_item_var

        row = self.build_one_grid_row(True)
        table_rows.append(row)

        # Now generate all the subtests, if they exist:
        sub_cases = ide_item.case.subcases
        self.n_ides_no_tests += bool(sub_cases)
        for i, sub_case in enumerate(sub_cases):
            self.next_row()
            is_last = i+1 == len(sub_cases)
            row = self.build_one_grid_row(False, sub_case=sub_case, is_last=is_last)
            table_rows.append(row)

        return table_rows



    def build_one_grid_row(self, is_root:bool, *, sub_case:dict=None, is_last:bool=False):
        """
        Build the html for one row of the css grid.

        @is_root: True for the "main" line/row (introduce the ide. May be the only line if
        no subcases)
        """
        row = [
            self.grid_cell_div(
                self.description() if is_root else self.description(sub_case, is_last=is_last)
            ),
            self.svg_feedback_cell(is_root, sub_case),
            self.buttons_cell(is_root),
            self.right_cell(is_root),
        ]
        return ''.join(row)


    def description(self, case:Case=None, *, is_last=False):
        """
        Build one test description html, with proper classes/ids/format.
        """
        is_root  = case is None
        desc     = case and case.get_description(False) or self.ide_item.case.get_description(True)
        div_desc = Html.div(desc, kls="pmt_note_tests" + ' top_test'*is_root + ' last'*is_last)

        if not is_root:
            return div_desc

        link = Html.a(self.ide_item.ide_name, href=self.ide_item.abs_link, target="_blank")
        return link + div_desc if desc else link


    def svg_feedback_cell(self, is_root:bool, sub_case:Optional[Case]):
        data    = {}
        classes = []
        has_svg = not is_root or not self.ide_item.case.subcases     # Means "this row has/is a test"

        if has_svg:
            case: Case = self.ide_item.case
            skipped = bool(
                sub_case.skip  if sub_case and sub_case.skip  is not None else
                sub_case.human if sub_case and sub_case.human is not None else
                case.skip  if case.skip is not None else
                case.human
            )
            state = Qcm.unchecked if skipped else Qcm.checked
            data.update({'state': state})
            self.css_rules.append(f"{ self.nth_row_var }:var(--display-{ state })")
            self.n_todo += not skipped

        if is_root:
            classes.append('top_test')

        cell = self.grid_cell_div(
            '' if not has_svg else Html.svg_qcm_box(data=data), kls=' '.join(classes),
        )
        return cell



    def buttons_cell(self, is_root:bool):
        cell_kls = f"test-btns { 'testing' * (not is_root) }".rstrip()
        load_btn = self._button('load_ide') if self.with_load_buttons else ""
        play_1   = self._button('test_1_ide', data={'i-ide': self.i_start_batch, 'i-row': self.i_row})
        cell     = self.grid_cell_div(load_btn + play_1, kls=cell_kls)
        self.rows_infos.append([self.i_start_batch, self.i_row+1])
        return cell


    def _button(self, kind:str, xtra_class:str="", **kw):
        return self.ide_tester.cls_create_button(
            self.env, kind, extra_btn_kls=xtra_class, style=self.nth_style, bare_tip=True, **kw
        )


    def right_cell(self, is_root:bool):
        cell = self.grid_cell_div(self._build_sections_boxes() if is_root else "")
        return cell


    def _build_sections_boxes(self):
        boxes = []
        for section in SECTIONS_BOXES_ORDER:
            test_code = bool(self.ide_item.case.code)
            kls_box   = 'orange-box'  if (
                section=='code' and test_code
                or section=='corr' and not test_code
            ) else ""
            box = Html.checkbox(
                getattr(self.ide_item.has, section),
                kls_box  = kls_box,
                tip_txt  = section + "?",
                bare_tip = True,
            )
            boxes.append(box)
        return Html.div(''.join(boxes), kls='sections-boxes')


    #--------------------------------------------------------------------------------


    def build_filters(self):
        """
        Div with the status filter toggle buttons/checkboxes.
        """
        return Html.div(
            (
                self._filter_btn('checked',   "", (Qcm.checked, "To do"))
              + self._filter_btn('unchecked', "", (Qcm.unchecked, "Skipped"))
              + self._filter_btn('correct',   "success", (Qcm.ok, "Passing"), (Qcm.fail_ok, "Should fail"))
              + self._filter_btn('incorrect', "failure", (Qcm.fail_test, "Fail"), (Qcm.pass_bad, "Should have failed"))
            ),
            id = HtmlClass.py_mk_tests_filters,
            kls = Qcm.multi,
        )


    def _filter_btn(self, kind:Qcm, txt:str, *svgs:Qcm):
        for svg_kls,_ in svgs:
            self.css_rules.append(f'--display-{ svg_kls }:unset')

        label = Html.div(f"Show{ '<br>'*bool(txt) }{ txt }", kls="filter-show")
        svgs_with_tip = [
            Html.svg_qcm_box(
                kls=HtmlClass.tooltip, data={'state': svg_kls, 'tip-txt':svg_tip}
            ) for svg_kls,svg_tip in svgs
        ]
        return Html.button(
            label + ''.join(svgs_with_tip),
            kls = "filter-btn",
            id = f"filter-{ kind }",
            data = {'states': '|'.join(kls for kls,_ in svgs)},
            active=1,
        )


    def build_global_controller(self):
        """
        Div containing the buttons and counters to control the tests (class contains "inline").
        """
        btn_start = self.ide_tester.cls_create_button(self.env, 'test_ides', bare_tip=True)
        btn_stop  = self.ide_tester.cls_create_button(self.env, 'test_stop', bare_tip=True)
        n_tests   = self.i_row+1 - self.n_ides_no_tests
        return f'''
<div class="inline" id="py_mk_tests_controllers">{ btn_start }{ btn_stop }
  <ul>
    <li>IDEs found: <span id="cnt-all">{ self.n_ides }<br>({ n_tests } cases)</span></li>
    <li>Skip:       <span id="cnt-unchecked" style="color:gray;">{ n_tests - self.n_todo }</span></li>
    <li>To do:      <span id="cnt-checked">{ self.n_todo }</span></li>
    <li>Success:    <span id="cnt-success" style="color:green;">0</span></li>
    <li>Error:      <span id="cnt-failed" style="color:red;">0</span></li>
  </ul>
  <button type="button" class="cases-btn" id="select-all">Select all</button>
  <br><button type="button" class="cases-btn" id="unselect-all">Unselect all</button>
  <br><button type="button" class="cases-btn" id="toggle-human">Toggle human</button>
</div>
'''
