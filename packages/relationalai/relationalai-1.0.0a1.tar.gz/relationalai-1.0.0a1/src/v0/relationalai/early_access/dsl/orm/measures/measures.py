from itertools import chain

from v0.relationalai.early_access.dsl.orm.measures.initializer import get_model, get_reasoner
from v0.relationalai.early_access.dsl.orm.models import Relationship, Role
from v0.relationalai.semantics.metamodel.util import ordered_set
import v0.relationalai.semantics as qb

from v0.relationalai.early_access.dsl.orm.measures.dimensions import Dimension, Splicer
from v0.relationalai.early_access.dsl.orm.measures.role_exprs import ComposeRoleExpr, NilRoleExpr, RoleExpr, SimpleRoleExpr, UnionRoleExpr

# Measures

class BaseMeasure:

    def __init__(self, m):
        if not isinstance(m, Role):
            raise Exception(f"Cannot classify {m} (or type {type(m)} as a base measure")

        self._reasoner = get_reasoner()

        c = m.player()
        if not c._is_primitive():
            raise Exception(f"Role {m} is played by {c}, which is not a value type; thus cannot classify {m} as a base measure")
        if not self._reasoner.is_one_role(m):
            raise Exception(f"Cannot classify role {m} as a base measure because it is spanned by an internel UC")
        self._measure_role = m
        self._dims = None

    def __call__(self, *args, **kwargs):
        return self.relationship()(*args, **kwargs)

    def dimensions(self):
        if self._dims is None:
            self._dims = [
                Dimension(r, rx())
                for r in self.measure_role().siblings()
            ]
        return self._dims

    def measure_role(self) -> Role:
        return self._measure_role

    def measure_type(self):
        return self._measure_role.player()

    def relationship(self):
        return self.measure_role()._part_of()
    
class Measure:

    # Create a new derived Measure by extending a sub-Measure (sub_measure) using
    # one or more dimension expressions to derive the dimensions of self from
    # those of sub_measure, aggregating the measurements so grouped by method.
    def __init__(self, sub_measure, *dim_exprs, method=qb.count):

        # Verify that m is a Measure, promoting Roles to BaseMeasures where
        # appropriate and throwing an exception if m is neither a Measure
        # nor a Role that denotes a BaseMeasure
        def check_measure(m):
            if isinstance(m, Role):
                # Then self derives from a base measure
                return BaseMeasure(m)
            else:
                # m should be a Measure...
                if not isinstance(m, Measure):
                    raise Exception(f"Tried to derive a measure from {m} of type {type(m)}, which is not a measure")
            return m

        self._sub_measure = check_measure(sub_measure)

        self._agg_method = method

        self._reasoner = get_reasoner()

        # Maps each Dimension (guid) to the Concept that the grouping role of the
        # Dimension is played by
        self._dimension_type = {}

        # Retains the dimension expressions declared to derive the dimensions of this
        # measure from those of the measure it derives from (self.sub_measure())
        self._dimension_exprs = dim_exprs

        # The ordered list of dimensions of this measure
        self._dims = []

        # A map from the guid of each Dimension in self._dims to that Dimension
        self._dimmap = {}

        # A map from the guid of each of this measure's dimensions 'd' to the root
        # dimension 'r' of the measure being derived from such that 'd' extends 'r',
        # either trivially or by applying some expression in self._dimension_exprs
        self._extends_sub_dimension = {}

        # The relationship that this measure generates.
        self._relationship = self._generate_relationship()

    def __call__(self, *args, **kwargs):
        return self._relationship(*args, **kwargs)

    def dimensions(self):
        if not self._dims:
            self._compute_dimensions()
        return self._dims

    def dimension_type(self, dim):
        return self._dimension_type[dim.guid()]

    # Returns the sub-dimension that dim (assumed to be a Dimension of self)
    # extends, or None
    def extends_sub_dimension(self, dim):
        dim_guid = dim.guid()
        if dim_guid in self._extends_sub_dimension:
            return self._extends_sub_dimension[dim_guid]
        
        return None

    # Returns true if dim is orthogonal to other dimensions in this measure.
    def orthogonal(self, dim):
        if not dim.mandatory():
            return False

        # An orthogonal dimension that is cut and that starts with the same
        #   measuring role as some other dimension, then it should be hidden
        r_guid = dim.measuring_role()._guid()
        return any(d2.measuring_role()._guid() == r_guid for d2 in self._dims)

    def measure_role(self) -> Role:
        return self.sub_measure().measure_role()

    def measure_type(self):
        return self.measure_role().player()

    def relationship(self):
        return self._relationship

    def sub_measure(self): return self._sub_measure

    # Internal methods

    def _add_dimension(self, dim):
        dim_guid = dim.guid()
        if dim_guid in self._dimmap:
            raise Exception(f"Cannot add the same Dimension ({dim.pretty_print}) to the same derived measure")
        self._dims.append(dim)
        self._dimmap[dim_guid] = dim

    def _add_dimension_type(self, dim, concept):
        dim_guid = dim.guid()
        if dim_guid in self._dimension_type:
            raise Exception(f"Error: Dimension {dim.pretty_print()} maps more than one type {str(self._dimension_type[dim_guid])} and {str(concept)}")
        else:
            self._dimension_type[dim_guid] = concept

    # Computes the dimensions of this measure by using the dimension expressions
    # named in this measure's declaration to extend (by either subsuming or splicing)
    # the dimensions of this measure's sub measure. We call these dimensions to splice
    # or extend "root" dimensions.
    def _compute_dimensions(self):

        # Partitions a list of dimensions into those that are exposed vs hidden
        def partition_hiddens(dims):
            hidden_dims = []
            exposed_dims = []
            for d in dims:
                if d.cuts():
                    hidden_dims.append(d)
                else:
                    exposed_dims.append(d)
            return exposed_dims, hidden_dims

        def check_used(used_exprs, exprs):
            if len(used_exprs) < len(exprs):
                unused_expr_seq = []
                for e in exprs:
                    if e.guid() not in used_exprs:
                        unused_expr_seq.append(e.pretty_print())
                unused_exprs = '{ ' + ",\n  ".join(unused_expr_seq) + '}'
                raise Exception(f"Attempted to derive a measure with incompatible dimension expressions: {unused_exprs}")

        # When invoked with a pair of the form (exposed_sub_dims, exprs) where:
        #
        #   * (exposed_sub_dims) is the ordered sequence of dimensions exposed
        #     by the sub measure; and
        #
        #   * exprs is a set of dimension expressions that self declares to
        #     either subsume or splice dimensions in exposed_sub_dims
        #
        # this function iterates through exposed_sub_dims in order, trying to apply
        # some dimension expression in exprs where possible.
        #
        # Returns any dimensions that extend some dimension in exposed_sub_dims but
        # which end in a cut.
        #
        def apply_all(exposed_sub_dims, exprs):
            cut_dims = []

            # Remember those expressions that were used to extend some sub dimension.
            # At the end of the loop, every expr from exprs should be used at least
            # once; otherwise the measure declaration is in error.
            used_exprs = ordered_set()

            for r in exposed_sub_dims:
                matched_root = False

                for e in exprs:
                    new_dim = r.extend_by(e)
                    if new_dim is not None:
                        if new_dim.cuts():
                            cut_dims.append(new_dim)
                        else:
                            self._add_dimension(new_dim)
                        self._extends_sub_dimension[new_dim.guid()] = r
                        matched_root = True
                        used_exprs.add(e.guid())

                if not matched_root:
                    self._extends_sub_dimension[r.guid()] = r
                    self._add_dimension(r)

            check_used(used_exprs, exprs)

            return cut_dims

        self._dims = []
        # First, partition the dimensions of the sub measure into two sets -- those that are
        # exposed and are therefore extendable -- and those that are hidden
        (exposed_sub_dims, hidden_roots) = partition_hiddens(self.sub_measure().dimensions())

        if len(exposed_sub_dims) == 0:
            raise Exception("Cannot derive a measure from a 0-dimensional measure")

        cut_dims = apply_all(exposed_sub_dims, self._dimension_exprs)

        # Get those hidden dimensions that are not orthogonal to any non-hidden
        # dimension of self, and add them as dimensions of self rather than
        # projecting them away.
        hidden_dims =  [d for d in cut_dims if not self.orthogonal(d)]
        for d in chain(hidden_dims, hidden_roots):
            self._add_dimension(d)

    def _generate_relationship(self) -> Relationship:
        value_type = self.measure_role().player()
        dims = self.dimensions()
        role_seq = []
        for i in range(len(dims)):
            player = dims[i].grouping_role_player()
            self._add_dimension_type(dims[i], player)
            role_str = ' {' + f"dim{i+1}:{player}" + '} '
            role_seq.append(role_str)
        madlib_prefix = " and ".join(role_seq)
        madlib = madlib_prefix + "maps to " + '{val:' + f"{value_type}" + '}'
        return get_model().Relationship(madlib)

def rx(*args) -> RoleExpr:
    if len(args) == 0:
        return NilRoleExpr()

    reasoner = get_reasoner()
    
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, Role):
            if not reasoner.is_one_role(arg):
                raise Exception(f"Role {arg} used in a dimension or splicer is not a one role")
            return SimpleRoleExpr(arg)
        else:
            return arg

    components = []

    for arg in args:
        if isinstance(arg, Role):
            if not reasoner.is_one_role(arg):
                raise Exception(f"Role {arg} used in a dimension or splicer is not a one role")
 
            components.append(SimpleRoleExpr(arg))
        else:
            components.append(arg)
        
    if len(components) == 1:
        return components[0]
    else:
        return ComposeRoleExpr(*components)

def star(*args): return rx(*args).star()
def plus(*args): return rx(*args).plus()

def dim(r, *args):
    return Dimension(r, rx(*args))

def splice(x, *args): return Splicer(x, rx(*args))

def union(*args): return UnionRoleExpr(*args)

def avg(m, *dims): return Measure(m, *dims, method = qb.avg)
def count(m, *dims): return Measure(m, *dims, method = qb.count)
def min(m, *dims): return Measure(m, *dims, method = qb.min)
def max(m, *dims): return Measure(m, *dims, method = qb.max)
def sum(m, *dims): return Measure(m, *dims, method = qb.sum)