from v0.relationalai.environments.base import except_return
from v0.relationalai.environments.ipython import IPythonEnvironment
import sys

class ColabEnvironment(IPythonEnvironment):
    remote = True

    @classmethod
    def detect(cls):
        return "google.colab" in sys.modules

    @except_return(Exception, None)
    def active_cell_id(self):
        return self.ipython.get_parent()["metadata"]["colab"]["cell_id"] #type: ignore
