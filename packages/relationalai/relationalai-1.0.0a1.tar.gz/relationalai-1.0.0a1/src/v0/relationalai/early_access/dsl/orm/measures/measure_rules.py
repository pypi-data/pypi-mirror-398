from abc import ABC, abstractmethod

import v0.relationalai.semantics as qb
from v0.relationalai.semantics import Expression
from v0.relationalai.early_access.dsl.core import warn


class MeasureGenerator:

    def __init__(self, measure):
        self._measure = measure

        # For that subset of Dimensions that extend some sub dimension trivially,
        # map the Dimension to that sub-measure Dimension so that both will use
        # the same variable in rules.
        self._dimension_unifies_with_sub_dimension = {}

        # For that subset of Dimensions that extend some sub dimension non-trivially,
        # maps the Dimension to the splicer that is used in the extension
        self._dimension_splices_simply = {}
        self._dimension_splices_star = {}
        self._dimension_splices_plus = {}

        self._analyze_dimensions()

        # The rules that this measure generates to derive self._relationship from
        # self.sub_measure()._relationship
        self._derivation_rules = []

        self._generate_rules()

    def measure(self): 
        return self._measure

    # Internal methods

    def _add_splice(self, dim, splicer):
        dguid = dim.guid()
        if splicer.simple():
            self._dimension_splices_simply[dguid] = splicer
        if splicer.kleene_star():
            self._dimension_splices_star[dguid] = splicer
        if splicer.kleene_plus():
            self._dimension_splices_plus[dguid] = splicer
            raise Exception("Splicers that do non-reflexive transitive closure (Kleene +) are not yet supported")
        if splicer.composer():
            raise Exception(f"Complex splicers not yet supported: {splicer.pretty_print()}")

    # Declare that dim in the Dimensions of self unifies with (uses same variable to join with)
    # sub_dim in the Dimensions of sub_measure
    def _add_unification(self, dim, sub_dim):
        self._dimension_unifies_with_sub_dimension[dim.guid()] = sub_dim

    # Analyze the dimensions of this measure with respect to those of the sub_measure to
    # determine:
    #  - Which dimensions of this measure should unify with a dimension of the sub measure; or
    #  - For dimensions of this measure that do not unify, what kind of dimensional splicing
    #    is require to extend paths that conform to the sub dimension into paths that conform
    #    to the extending dimension.
    def _analyze_dimensions(self):
        measure = self.measure()
        for d in measure.dimensions():
            sub_dim = measure.extends_sub_dimension(d)
            if sub_dim is not None:
                x, y = d.subsumes(sub_dim)
                assert(x is not None)
                if y is not None:
                    self._add_splice(d, y)
                else:
                    self._add_unification(d, sub_dim)

    def _generate_rules(self):
        measure = self.measure()
        navigation_dims = [d for d in measure.dimensions() if d.guid() in self._dimension_splices_simply]
        self._derivation_rules.append(SimpleMeasureRule(self, *navigation_dims))

        if len(self._dimension_splices_star) > 0:
            # We need to generate a base rule for the recursion and one recursive rule for
            # each Kleene *.
            for d in self._dimension_splices_star:
                self._derivation_rules.append( RecursiveStepMeasureRule(self, measure._dimmap[d]) )


class MeasureRule(ABC):

    def __init__(self, measure_gen):
        self._measure_generator = measure_gen
        self._measure = measure_gen.measure()
        self._sub_measure = self._measure.sub_measure()

        # Maps each Dimension (dim) of either this measure or its sub-measure
        #   to the Variable that will range over nodes that terminate paths that conform to dim
        self._dimension_variables = {}

        # We use this map to decide when to duplicate refs to Concepts
        #   to generate distinct variables of the same Concept type
        self._varname_to_dim = {}

        self._sub_measurement_variable = self.measure().measure_type()

    def dimension_var(self, dim):
        return self._dimension_variables[dim.guid()]

    def measure(self): return self._measure
    def measure_generator(self): return self._measure_generator
    def sub_measure(self): return self.measure().sub_measure()

    # Internal methods

    # Every measure rule involves at least one level-mapping atom unless the measure
    #   merely cuts dimensions of the sub measure. This hook method generates all of
    #   the level-mapping atoms to use in this rule
    @abstractmethod
    def _generate_level_mapping_atoms(self) -> list[Expression]:
        pass

    # Every measure rule uses a sub-measure atom to look up the measurements to aggregate.
    # Hook method that generates the sub-measure atom
    @abstractmethod
    def _generate_sub_measure_atom(self) -> Expression:
        pass

    # Hook method that generates a Variable to range over each measure
    # and sub-measure Dimension. Different subclasses of MeasureRule
    # implement this differently to unify measure and sub-measure
    # dimensions in different ways
    @abstractmethod
    def _map_dimensions_to_vars(self):
        pass

    def _generate(self):
        self._map_dimensions_to_vars()
        self._sub_measure_atom = self._generate_sub_measure_atom()
        self._level_mapping_atoms = self._generate_level_mapping_atoms()

        # Group the aggregated measurements by the measure's dimensions.
        measure_dim_vars = [self._dimension_variables[d.guid()] for d in self.measure().dimensions()]
        # Distinguish the sub-measurements to aggregate by the sub_measure's dimensions.
        sub_measure_dim_vars = [self._dimension_variables[d.guid()] for d in self.sub_measure().dimensions()]
        assert self._sub_measure_atom is not None, "Sub-measure atom must be generated before aggregation"
        agg = (
            self._measure._agg_method(*sub_measure_dim_vars, self._sub_measurement_variable)
                .per(*measure_dim_vars)
                .where(
                    self._sub_measure_atom._op(*self._sub_measure_atom._params),
                    *[
                        atom._op(*atom._params)
                        for atom in self._level_mapping_atoms
                    ]
                )
        )
        self._measure_atom = self._generate_measure_atom(self.measure(), self.measure().dimensions(), agg)

        # Generate QB rule
        qb.define( self._measure_atom ).where( agg )

    # Generates an atom that 
    def _generate_level_mapping_atom(self, role, dim):
        measure = self.measure()
        subdim = measure.extends_sub_dimension(dim)
        dvar = self.dimension_var(dim)
        sdvar = self.dimension_var(subdim)
        expected_sdtype = role.sibling().player()
        if self._measure._reasoner.in_subtype_closure(expected_sdtype, sdvar):
            sdvar = expected_sdtype(sdvar)
        return role._part_of()(sdvar, dvar) if role._field_ix == 1 else role._part_of()(dvar, sdvar)

    def _generate_measure_atom(self, measure, dim_seq, value_var) -> Expression:
        # [REKS: TODO] Need to properly check the role ordering to guarantee we generate
        #              a correctly sequenced atom, at which point we can safely remove
        #              this warning
        # warn("Generating a measure atom whose correctness assumes the measure role appears last in the relationship")

        for d in dim_seq:
            dim_guid = d.guid()
            if dim_guid not in self._dimension_variables:
                warn(f"++ Could not map dimension {d.pretty_print()} to a variable")
        # Get the sequence of dimensional variables to use in the atom
        var_seq = [ self.dimension_var(d) for d in dim_seq ]
        return measure.relationship()(*var_seq, value_var)

    # Generates a Variable to use to range over nodes that terminate paths that conform
    # to Dimension dim.
    def _generate_var_for_dimension(self, dim):
        var = dim.grouping_role_player()
        
        # Ensure the Variable we return is unique to dim
        if str(var) in self._varname_to_dim:
            var = var.ref()

        self._varname_to_dim[str(var)] = dim
        self._dimension_variables[dim.guid()] = var

        return var

# Instances of this class generate a non-recursive rule that extends sub-measure paths using
# splicers along the named dimensions assuming there are no other rules used to derive
# this measure
class SimpleMeasureRule(MeasureRule):

    def __init__(self, measure, *dims):
        super().__init__(measure)
        self._extends = dims
        self._generate()

    def _generate_sub_measure_atom(self) -> Expression:
        return self._generate_measure_atom(self.sub_measure(),
                                           self.sub_measure().dimensions(),
                                           self._sub_measurement_variable)

    def _generate_level_mapping_atoms(self) -> list[Expression]:
        atoms = []
        # Generate the atoms used to navigate up each dimension extension
        for d in self._extends:
            splicer = self.measure_generator()._dimension_splices_simply[d.guid()]
            role = splicer._role
            atoms.append(self._generate_level_mapping_atom(role, d))
        return atoms

    # Internal methods

    def _unifies_with(self, dim):
        dim_guid = dim.guid()
        measure = self.measure()
        measure_gen = self.measure_generator()
        if dim_guid in measure_gen._dimension_unifies_with_sub_dimension:
            return measure_gen._dimension_unifies_with_sub_dimension[dim_guid]
        if dim_guid in measure_gen._dimension_splices_star:
            return measure.extends_sub_dimension(dim)
        return None

    def _map_dimensions_to_vars(self):
        for d in self.measure().dimensions():
            var = self._generate_var_for_dimension(d)
            sub_dim = self._unifies_with(d)
            if sub_dim is not None:
                self._dimension_variables[sub_dim.guid()] = var

        for sub_dim in self.sub_measure().dimensions():
            if sub_dim.guid() not in self._dimension_variables:
                self._generate_var_for_dimension(sub_dim)

class RecursiveStepMeasureRule(MeasureRule):

    def __init__(self, measure, dim):
        super().__init__(measure)
        self._extends = dim
        self._generate()

    def _generate_level_mapping_atoms(self) -> list[Expression]:
        # Generate the atom used to navigate up each dimension extension
        dim = self._extends
        splicer = self.measure_generator()._dimension_splices_star[dim.guid()]
        role = splicer.role_body()
        return [ self._generate_level_mapping_atom(role, dim) ]

    def _generate_sub_measure_atom(self) -> Expression:
        measure = self.measure()
        dim_seq = []
        ext_guid = self._extends.guid()
        dim_seq.extend(
            self._body_dim if d.guid() == ext_guid else d
            for d in measure.dimensions()
        )
        return self._generate_measure_atom(measure, dim_seq, self._sub_measurement_variable)

    def _map_dimensions_to_vars(self):
        measure = self.measure()
        for d in measure.dimensions():
            self._generate_var_for_dimension(d)

        sub_dim = measure.extends_sub_dimension(self._extends)
        self._generate_var_for_dimension(sub_dim)

        self._body_dim = sub_dim