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

# pylint: disable=all

from typing import Any, Dict, Optional

from ..exceptions import PmtInternalError
from ..tools_and_constants import HtmlClass




def _build_html_attributes(
    id:str,
    kls:str,
    attrs: Dict[str, str],
    # disabled: Any=None,
    # checked: Any=None,
    kwargs: Dict[str,Any],
):
    """
    Build a string with all the desired html attributes for an opening tag.

    * Automatically add an id if the argument is truthy.
    * Automatically add a class string if the kls argument is truthy.
    * Any kwargs is converted to the related html attribute.
    * If disabled or checked are used in the kwargs (even falsy!), they are added as bare string
      attributes (hence without explicit value, hence equivalent to checked="checked").
    * The attrs dict allow to define kebab-cased attributes. Note that any attribute defined from
      kwargs _and_ attrs will give the priority to the version defined in the kwargs.
    * If `data` is used as kwargs, it has to be a dict[str,Any], that will be automatically
      converted to `data-name="value"` pairs. These will have priority on any equivalent value
      defined through the attrs argument.
    """
    attrs = attrs or {}
    attrs.update(kwargs)
    if id:  attrs['id'] = id
    if kls: attrs['class'] = kls

    if 'data' in attrs:
        data: Dict = attrs.pop('data')
        attrs.update({f'data-{ k }':v for k,v in data.items()})

    suffix_attrs = ""
    for name in ('disabled', 'checked'):
        if name in attrs:
            attrs.pop(name)
            suffix_attrs += f" { name }"

    attributes = " ".join(
        f'{ name }="{ value }"'
        for name,value in attrs.items()
    ) + suffix_attrs

    return attributes



def html_builder_factory(template:str, allow_content):
    def tagger(tag:str, **props):
        def html_builder(
            content:str="",
            *,
            id:     str = '',
            kls:    str = "",
            attrs:  Dict[str, str]=None,
            **kwargs
            # disabled: Any = None
            # checked:  Any = None
        ) -> str:
            """
            Build a the code for the given tag element.

            NOTE: Using the @content argument on "mono tags" will raise ValueError.
            """
            if not allow_content and content:
                raise ValueError(f"Cannot use content on {tag!r} tags ({content=!r})")
            attributes = _build_html_attributes(id, kls, attrs, kwargs)
            code = template.format(tag=tag, content=content, attributes=attributes)
            return code

        return html_builder
    return tagger



mono_tag = html_builder_factory("<{tag} {attributes} />", False)
bi_tag   = html_builder_factory("<{tag} {attributes}>{content}</{tag}>", True)




input   = mono_tag('input')
img     = mono_tag('img')

a       = bi_tag('a')
button  = bi_tag('button', type='button') # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button#notes
code    = bi_tag('code')
div     = bi_tag('div')
script  = bi_tag('script')
style   = bi_tag('style')
span    = bi_tag('span')
svg     = bi_tag('svg')
td      = bi_tag('td')





def tooltip(txt:str, width_em:Optional[int]=None, shift:Optional[int]=None, tip_side='bottom'):
    """
    Generic PMT tooltip builder. If width_em is falsy, use automatic width.
    Th @shift argument is the % to use for the translation, 0% means the tooltip will be the right,
    100% means it will go on the left. With 50 (default), it's centered below the original element.
    """
    if shift is None:
        shift = 50
    dct = {
        'kls': f'tooltiptext { tip_side }',
        'style': f'--tool_shift: {shift}%;',
    }
    if width_em:
        dct['style'] += f"width:{ width_em }em;"

    return span(txt, **dct)



def checkbox(
    checked:bool,
    *,
    label:str="",
    id:str = "none",
    kls:str = "",
    kls_box:str = "",
    tip_txt:str = "",
    width_em:Optional[int]=None,
    tip_shift:Optional[int]=None,
    bare_tip: bool = False
):
    """
    Build a checkbox with a PMT tooltip attached, and an optional label after it.
    If @bare_tip is True and there is no given label, attach the tooltip info as dataset
    directly on the input.
    """
    input_kw = {'checked':""} if checked else {}

    if bare_tip:
        if label or kls:
            raise PmtInternalError(
                "A checkbox built with @bare_tip=True shouldn't have a label or a class for any outer element."
            )
        dct = {}
        if tip_txt:
            dct['data-tip-txt'] = tip_txt
            if width_em is not None: dct['data-tip-width'] = width_em
        input_kw.update(dct)
        kls_box = f"{ kls_box } { HtmlClass.tooltip }".lstrip()
    else:
        txt = label and span(label)
        tip = tooltip(tip_txt, width_em, shift=tip_shift)

    box = input('', type='checkbox', disabled=True, id=id, kls=kls_box, **input_kw)
    return box if bare_tip else div( box+txt+tip, kls=f'{ HtmlClass.tooltip } { kls }'.rstrip() )






SVG_BOX_TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg {attrs} viewBox="0 0 12 12" role="img" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" style="stroke-width:1.25;stroke-linecap:round">
<path class="bgd-svg" style="fill:var(--qcm-fill);stroke:none;" d="M 5.93,1.93 3.29,2.40 2.70,2.75 1.86,5.70 2.38,8.76 2.75,9.29 5.82,10.13 9.07,9.45 9.36,9.13 10.12,6.11 9.49,2.93 9.12,2.65 Z"></path>
<g style="fill:var(--qcm-light);stroke:var(--qcm-light)">
 <path class="tick" style="display:var(--tick);stroke-width:0;stroke-linecap:butt;stroke-linejoin:round" d="M 6.34,8.49 C 6.49,7.32 7.07,5.36 9.05,4.06 L 8.93,3.91 C 7.13,4.50 6.38,5.52 5.63,7.03 5.36,6.61 3.91,5.92 3.47,5.86 L 3.32,6.00 C 4.41,6.54 5.06,7.30 5.63,8.77"></path>
 <g style="display:var(--cross);" transform="matrix(0.91,0,0,0.91,0.52,0.52)">
  <rect width="8.33" height="0.59" x="-5.86" y="8.02" transform="rotate(-56.54)"></rect>
  <rect width="8.33" height="0.59" x="-12.47" y="-1.99" transform="matrix(-0.55,-0.83,-0.83,0.55,0,0)"></rect>
 </g>
</g>
<g style="fill:none;stroke:var(--qcm-border)">{shape}</g>
</svg>'''
CIRCLE_QCS = '<circle cy="6" cx="6" r="4.2"></circle>'
SQUARE_QCM = '<rect width="7.41" height="7.36" x="2.29" y="2.32"></rect>'


def svg_qcm_box(
    is_multi: bool=True,
    id: str = "",
    kls: str = "",
    attrs: Dict[str,Any] = None,
    **kwargs
):
    shape = SQUARE_QCM if is_multi else CIRCLE_QCS
    attributes = _build_html_attributes(id, f'qcm {kls}'.rstrip(), attrs, kwargs)
    return SVG_BOX_TEMPLATE.format(attrs=attributes, shape=shape)
