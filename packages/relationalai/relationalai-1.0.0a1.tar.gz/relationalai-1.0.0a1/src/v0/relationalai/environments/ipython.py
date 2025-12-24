from __future__ import annotations
import contextlib
import io
import sys
import warnings
from v0.relationalai.environments.base import NotebookCell, NotebookRuntimeEnvironment, except_return, handle_rai_exception, handle_rai_warning, patch

class IPythonEnvironment(NotebookRuntimeEnvironment):
    def __init__(self):
        from IPython import get_ipython # type: ignore
        self.ipython = get_ipython()
        super().__init__()

    @classmethod
    @except_return(ImportError, False)
    def detect(cls):
        from IPython import get_ipython # type: ignore
        return bool(get_ipython())

    @except_return(Exception, None)
    def active_cell_id(self):
        meta = self.ipython.get_parent()["metadata"]
        return meta.get("cellId", meta.get("cell_id")) #type: ignore

    def _patch(self):
        self.ipython.events.register("pre_run_cell", self._pre_run_cell)
        self.ipython.events.register('post_run_cell', self._post_run_cell)

        @patch(warnings, "showwarning")
        def _(original, message, category, filename, lineno, file=None, line=None):
            if not handle_rai_warning(message):
                original(message, category, filename, lineno, file, line)

        self.ipython.set_custom_exc((BaseException,), self._handle_exc)

    def _handle_exc(self, shell, exc_type, exc_value, exc_traceback, tb_offset=1):
        from ..errors import RAIException

        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            handle_rai_exception(exc_value)

        if isinstance(exc_value, RAIException):
            pprinted = buffer.getvalue().strip()
            # remove the trailing divider
            pprinted = pprinted[:pprinted.rfind("\n")]
            print(pprinted, file=sys.stderr)

        else:
            shell.showtraceback((exc_type, exc_value, exc_traceback), tb_offset=tb_offset)

    def _pre_run_cell(self, info):
        self.update_cell(self._cell_from_exec_info(info))

    @except_return(Exception, None)
    def _post_run_cell(self, result):
        from .. import dsl
        graph = dsl.get_graph()
        if graph._temp_is_active():
            graph._flush_temp()
            graph._restore_temp()

    def _cell_from_exec_info(self, info):
        cell_id = getattr(info, "cell_id", None) or getattr(info, "cellId", None)
        if cell_id:
            in_ns = self.ipython.user_ns['In']
            cell_ix = len(in_ns)
            cell = NotebookCell(cell_id, f"In[{cell_ix}]", getattr(info, "raw_cell", lambda: in_ns[cell_ix]))
            return cell
