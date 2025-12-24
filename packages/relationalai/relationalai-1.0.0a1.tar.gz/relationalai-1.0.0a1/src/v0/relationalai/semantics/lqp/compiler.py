#--------------------------------------------------
# Compiler
#--------------------------------------------------

from v0.relationalai.semantics.lqp import ir as lqp, model2lqp
from v0.relationalai.semantics.lqp.utils import TranslationCtx, UniqueNames
from v0.relationalai.semantics.lqp.passes import lqp_passes
from v0.relationalai.semantics.metamodel import ir, compiler as c

from typing import Optional

class Compiler(c.Compiler):
    def __init__(self):
        super().__init__(lqp_passes())
        self.def_names = UniqueNames()

    def do_compile(self, model: ir.Model, options:dict={}) -> tuple[Optional[tuple], lqp.Epoch]:
        fragment_id: bytes = options.get("fragment_id", bytes(404))
        # Reset the var context for each compilation
        # TODO: Change to unique var names per lookup
        # TODO: Have our needs realigned with NameCache?
        return model2lqp.to_lqp(model, fragment_id, TranslationCtx(self.def_names))
