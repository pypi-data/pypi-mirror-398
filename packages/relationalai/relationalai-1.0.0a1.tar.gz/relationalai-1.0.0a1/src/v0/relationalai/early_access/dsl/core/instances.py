from v0.relationalai.early_access.dsl.core.exprs import Expr


class Instance(Expr):

    def __init__(self, c, arglist):
        self.concept = c
        self.arglist = arglist

    def entityid(self):
        arghashes = []
        for c in self.arglist:
            if isinstance(c, Instance):
                arghashes.append(c.entityid())
            else:
                arghashes.append(c)
        return hash((self.concept.entityid(), *arghashes))

    def display(self):
        params = []
        for i in range(len(self.arglist)):
            arg = self.arglist[i]
            if isinstance(arg, Instance):
                params.append(arg.pprint())
            else:
                # Otherwise, arg must be a constraint of some UnconstrainedValueType
                if isinstance(arg, str):
                    params.append(f"\"{arg}\"")
                else:
                    params.append(arg)
        return self.concept.ctor_name() + '[' + ",".join(params) + ']'

    def pprint(self):
        return self.display()


class ValueTypeInstance(Instance):

    def __init__(self, vtype, arglist):
        if len(arglist) != len(vtype._params):
            raise Exception(
                f"Value type {vtype.name()} constructor maps tuples of length {len(vtype.constructor())} but was "
                f"instantiated with {len(arglist)} arguments")
        Instance.__init__(self, vtype, arglist)
