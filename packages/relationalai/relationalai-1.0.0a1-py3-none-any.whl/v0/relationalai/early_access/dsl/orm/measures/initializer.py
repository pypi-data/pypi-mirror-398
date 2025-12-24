import threading
from v0.relationalai.early_access.dsl.orm.models import Model

_model = threading.local()

def init_measure_service(model: Model):
    _model.instance = model

def get_model():
    try:
        return _model.instance
    except AttributeError:
        raise RuntimeError("Measure service is not initialized. Call init_measure_service() before using it.")
    
def get_reasoner():
    return get_model().reasoner()