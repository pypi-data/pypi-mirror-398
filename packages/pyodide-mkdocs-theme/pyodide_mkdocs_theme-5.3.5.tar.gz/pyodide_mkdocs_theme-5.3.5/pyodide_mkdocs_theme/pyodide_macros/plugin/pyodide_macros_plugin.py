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


from inspect import signature, Parameter
from functools import wraps
from pathlib import Path


from jinja2 import Environment
from mkdocs.config.defaults import MkDocsConfig
from mkdocs_macros.plugin import MacrosPlugin
from mkdocs.structure.nav import Navigation
from mkdocs.structure.files import Files



from ...__version__ import __version__
from ..pyodide_logger import logger
from ..plugin_tools import test_cases
from ..plugin_tools.macros_data import MacroData, MacroDataSqlide
from .maestro_base import BaseMaestro
from .maestro_files import MaestroFiles
from .maestro_meta import MaestroMeta
from .maestro_indent import MaestroIndent
from .maestro_macros import MaestroMacros
from .maestro_templates import MaestroTemplates
from .maestro_contracts import MaestroContracts
from ..macros import (
    IDEs,
    figure,
    py_script,
    qcm,
)







# NOTE: declaring the full inheritance chain isn't really needed, but it's a cool reminder... :p
class PyodideMacrosPlugin(
    MaestroContracts,
    MaestroTemplates,
    MaestroMacros,
    MaestroIndent,
    MaestroMeta,
    MaestroFiles,
    BaseMaestro,
    MacrosPlugin,    # Always last, so that other classes may trigger super methods appropriately.
):
    """
    Class centralizing all the behaviors of the different parent classes.

    This is kinda the "controller", linking all the behaviors to mkdocs machinery, while the
    parent classes hold the "somewhat self contained" behaviors.

    For reference, here are the hooks defined in the original MacrosPlugin:
        - on_serve
        - on_config
        - on_nav
        - on_page_markdown  (+ on_pre_page_macros + on_post_page_macros)
        - on_post_build     (on_post_build macros)
    """

    is_dirty: bool

    def on_startup(self, command:str, dirty:bool):
        self.in_serve = command == 'serve' #and False   # Uncomment to simulate a build while doing a serve
        self.is_dirty = dirty                           # pylint: disable=attribute-defined-outside-init



    # Override
    @logger.hook(enable_catch=True)
    def on_config(self, config:MkDocsConfig):
        # --------------------------------------------------------------
        # pylint: disable=attribute-defined-outside-init
        # Section to always apply first:

        self._conf            = config # done in MacrosPlugin, but also here because needed here or there
        self.language         = config.theme['language']
        self.docs_dir_path    = Path(config.docs_dir)
        self.docs_dir_cwd_rel = self.docs_dir_path.relative_to(Path.cwd())
        # --------------------------------------------------------------

        super().on_config(config)

        MacroData.register_config(self)
        logger.info("Plugin configuration ready.")


    #--------------------------------------------------------------------------
    # Define all hooks and call their super method, making sure the decoration is always at the top level

    @logger.hook
    def on_files(self, files: Files, /, *, config: MkDocsConfig):
        return super().on_files(files, config=config)

    @logger.hook
    def on_nav(self, nav: Navigation, /, *, config: MkDocsConfig, files: Files):
        return super().on_nav(nav, config=config, files=files)

    @logger.hook
    def on_env(self, env:Environment, config:MkDocsConfig, files:Files):
        return super().on_env(env, config=config, files=files)

    @logger.hook
    def on_post_build(self, config: MkDocsConfig):
        return super().on_post_build(config)

    #--------------------------------------------------------------------------



    # Override
    def _load_modules(self):
        """ Override the super method to register the Pyodide macros at appropriate time """

        logger.info("Register PMT macros/classes.")
        macros = [
            IDEs.IDE,
            IDEs.IDEv,
            IDEs.IDE_tester,
            IDEs.IDE_playground,
            IDEs.terminal,
            IDEs.py_btn,
            IDEs.run,
            figure.figure,
            py_script.section,
            py_script.composed_py,
            py_script.py,
            qcm.multi_qcm,
        ]

        # Register all theme's macros:
        for func in macros:
            self.macro(func(self))

        self.macro(test_cases.Case)     # Not a macro, but needed in the jinja environment

        # If mkdocs-sqlite-console is registered as plugin for the project, automatically add
        # the macro to the environment (requires sqlite-console > 1.0.7)
        if self.use_sqlite_console:
            sql = self._conf.plugins['sqlite-console']
            if hasattr(sql, 'sqlide'):      # Do not register earlier versions of the plugin (no macro support)
                sqlide = self._conf.plugins['sqlite-console'].sqlide
                self.macro(sqlide)

        # def macro_with_warning(func):
        #     macro = func(self)
        #     logged = False          # log once only per macro...
        #
        #     @wraps(func)
        #     def wrapper(*a,**kw):
        #         nonlocal logged
        #         if not logged:
        #             logged = True
        #             self.warn_unmaintained(f'The macro {func.__name__!r}')
        #         return macro(*a,**kw)
        #     return wrapper

        # old_macros = []                 # Kept in case becomes useful again one day...
        # for func in old_macros:
        #     self.macro( macro_with_warning(func) )

        logger.info("Register user's macros.")
        super()._load_modules()



    # Override
    def _load_yaml(self):
        """
        Override the MacrosPlugin method, replacing on the fly `__builtins__.open` with a version
        handling the encoding.
        """
        # pylint: disable=multiple-statements
        src_open = open
        def open_with_utf8(*a,**kw):
            kw['encoding'] = self.load_yaml_encoding
            return src_open(*a, **kw)

        # Depending on the python version/context, the __builtins__ can be of different types
        as_dct = isinstance(__builtins__, dict)
        try:
            if as_dct:  __builtins__['open'] = open_with_utf8
            else:       __builtins__.open = open_with_utf8
            super()._load_yaml()
        finally:
            if as_dct:  __builtins__['open'] = src_open
            else:       __builtins__.open = src_open
