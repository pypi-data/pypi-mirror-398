#
# The names used to refer to components of a schema. Always involves a name,
# zero or more dashes (' symbols in Z), and a prefix string that could be
# empty.
#
from v0.relationalai.early_access.dsl.constants import PRIME


class CompName:

    # Generates a CompName from a name *nm* in context *ctx* in which the
    # component is declared and a level *i* that is between 0 and the depth
    # of ctx. The CompName at level i must reflect the cumulative decorations
    # (dashes and prefixes) that were applied at levels i .. d.
    #
    @staticmethod
    def gen_from_context(nm, ctx, i, dashes=0):

        dsh = ctx.dashes[i] + dashes
        pref = ctx.prefixes[i]
        return CompName(nm, dashes=dsh, prefix=pref)

    def __init__(self, nm, dashes=0, prefix=""):
        self.name = nm
        self.prefix = prefix
        self.dashes = dashes

    def display(self):
        if self.prefix == "":
            nm = self.name
        else:
            nm = self.name[0].capitalize() + self.name[1:]
        return self.prefix + nm + PRIME * self.dashes

    # This predicate returns True if this name is decorated by a single dash
    #
    def decorated(self) -> bool:
        return self.dashes == 1

    def undecorated(self) -> bool:
        return self.dashes == 0

    def undash(self):
        dashes = self.dashes - 1
        if dashes < 0:
            raise Exception(f"++ Cannot undash {self.display()}")
        else:
            return CompName(self.name, dashes, self.prefix)

    def entityid(self):
        return hash(self.display())
