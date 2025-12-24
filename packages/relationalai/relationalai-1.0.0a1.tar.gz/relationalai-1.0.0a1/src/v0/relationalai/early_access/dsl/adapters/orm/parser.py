import json
import re
import warnings

import xmltodict
from collections import defaultdict
from v0.relationalai.early_access.dsl.adapters.orm.model import ORMEntityType, ORMValueType, ORMRole, ORMSubtypeFact, \
    ORMUniquenessConstraint, ORMExclusionConstraint, ORMMandatoryConstraint, ORMReadingRole, ORMReading, \
    ExclusiveInclusiveSubtypeFact, InclusiveSubtypeFact, ExclusiveSubtypeFact, SubtypeFact, ORMInclusionConstraint, \
    ORMRoleValueConstraint, ORMValueComparisonConstraint, ORMValueComparisonOperator, ORMRingConstraint, ORMRingType, \
    ORMRoleSubsetConstraint, ORMInclusiveRoleConstraint, ORMExclusiveRoleConstraint, ORMEqualityConstraint, \
    ORMFrequencyConstraint, ORMCardinalityConstraint, ORMRange, ORMRoleCardinalityConstraint, \
    ORMValueTypeValueConstraint
from v0.relationalai.semantics.metamodel.util import ordered_set
from v0.relationalai.util.graph import topological_sort


class ORMParser:

    def __init__(self, orm_file_path):
        with open(orm_file_path) as orm_file:
            data = xmltodict.parse(orm_file.read())

        self._ontology = json.loads(json.dumps(data))

        self._role_to_player = dict()
        self._cardinality_constraints = dict()
        self._role_cardinality_constraints = dict()
        self._value_type_value_constraints = dict()

        self._model_name = self._parse_model_name()
        self._entity_types = self._parse_entity_types()
        self._value_types = self._parse_value_types()
        self._object_types = {**self._value_types, **self._entity_types}
        self._roles, self._ignored_roles = self._parse_roles()
        self._fact_type_to_roles = self._parse_fact_type_to_roles()
        self._role_value_constraints = self._parse_role_value_constraints()
        self._internal_uniqueness_constraints, self._external_uniqueness_constraints = self._parse_uniqueness_constraints()
        (self._unique_roles, self._fact_type_to_internal_ucs, self._fact_type_to_complex_ucs,
         self._identifier_fact_type_to_entity_type) = self._process_internal_uniqueness_constraints()
        self._exclusion_constraints = self._parse_exclusion_constraints()
        self._inclusion_constraints = self._parse_inclusion_constraints()
        self._inclusive_role_constraints = self._parse_inclusive_role_constraints()
        self._exclusive_role_constraints = self._parse_exclusive_role_constraints()
        self._mandatory_constraints = self._parse_mandatory_constraints()
        self._ring_constraints = self._parse_ring_constraints()
        self._frequency_constraints = self._parse_frequency_constraints()
        self._value_comparison_constraints = self._parse_value_comparison_constraints()
        self._role_subset_constraints = self._parse_role_subset_constraints()
        self._equality_constraints = self._parse_equality_constraints()
        self._subtype_facts = self._parse_subtype_facts()
        self._sorted_subtype_facts = self._sort_subtype_facts()
        self._fact_type_readings = self._parse_fact_types_reading_orders()
        self._mandatory_roles = self._parse_mandatory_roles()
        self._object_types_to_cardinality_constraints = self._parse_object_types_to_cardinality_constraints()

    def model_name(self):
        return self._model_name

    def entity_types(self) -> dict[str, ORMEntityType]:
        return self._entity_types

    def object_types(self):
        return self._object_types

    def value_types(self):
        return self._value_types

    def roles(self):
        return self._roles

    def role_value_constraints(self):
        return self._role_value_constraints

    def subtype_facts(self):
        return self._subtype_facts

    def external_uniqueness_constraints(self):
        return self._external_uniqueness_constraints

    def value_comparison_constraints(self):
        return self._value_comparison_constraints

    def inclusion_constraints(self):
        return self._inclusion_constraints

    def exclusion_constraints(self):
        return self._exclusion_constraints

    def inclusive_role_constraints(self):
        return self._inclusive_role_constraints

    def exclusive_role_constraints(self):
        return self._exclusive_role_constraints

    def ring_constraints(self):
        return self._ring_constraints

    def frequency_constraints(self):
        return self._frequency_constraints

    def role_subset_constraints(self):
        return self._role_subset_constraints

    def equality_constraints(self):
        return self._equality_constraints

    def cardinality_constraints(self):
        return self._cardinality_constraints

    def value_type_value_constraints(self):
        return self._value_type_value_constraints
    
    def role_cardinality_constraints(self):
        return self._role_cardinality_constraints

    def unique_roles(self):
        return self._unique_roles

    def mandatory_roles(self):
        return self._mandatory_roles

    def fact_type_readings(self):
        return self._fact_type_readings

    def fact_type_to_internal_ucs(self):
        return self._fact_type_to_internal_ucs

    def fact_type_to_complex_ucs(self):
        return self._fact_type_to_complex_ucs

    def fact_type_to_roles(self):
        return self._fact_type_to_roles

    def identifier_fact_type_to_entity_type(self):
        return self._identifier_fact_type_to_entity_type

    def sorted_subtype_facts(self):
        return self._sorted_subtype_facts

    def objects_type_to_cardinality_constraints(self):
        return self._object_types_to_cardinality_constraints

    def _parse_fact_type_to_roles(self):
        fact_type_data = defaultdict(list)
        for role in self._roles.values():
            relationship_name = role.relationship_name
            fact_type_data[relationship_name].append(role)
        return fact_type_data

    def _parse_object_types_to_cardinality_constraints(self):
        object_types_constraints = {}
        for cc in self._cardinality_constraints.values():
            object_type_name = self._object_types[cc.object_type].name
            object_types_constraints[object_type_name] = cc
        return object_types_constraints

    def _parse_model_name(self):
        model_name = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel", "@Name")
        return model_name if model_name else "ORMModel"

    def _parse_entity_types(self):
        entity_types = {}
        orm_entity_types = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                            "orm:Objects", "orm:EntityType")
        if orm_entity_types:
            for et in self._single_object_to_list(orm_entity_types):
                id = et["@id"]
                name = et['@Name']
                ref_mode = et.get("@_ReferenceMode") or None
                entity_types[id] = ORMEntityType(id, name, ref_mode)
                self._parse_role_to_player_reference(et)
                self._parse_cardinality_constraint(et)
        return entity_types

    def _parse_value_types(self):
        value_types = {}
        data_types = self._parse_data_types()
        orm_value_types = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                           "orm:Objects", "orm:ValueType")
        if orm_value_types:
            for vt in self._single_object_to_list(orm_value_types):
                if not vt.get("@IsImplicitBooleanValue"):
                    id = vt["@id"]
                    name = vt["@Name"]
                    data_type = data_types[self._get_nested(vt, "orm:ConceptualDataType", "@ref")]
                    value_types[id] = ORMValueType(id, name, data_type)
                    self._parse_role_to_player_reference(vt)
                    self._parse_cardinality_constraint(vt)
                    self._parse_value_type_value_constraints(vt)
        return value_types

    def _parse_value_type_value_constraints(self, vt):
        vt_id = vt.get("@id")
        value_constraint = self._get_nested(vt,  "orm:ValueRestriction", "orm:ValueConstraint")
        if value_constraint:
            vc_id = value_constraint.get("@id")
            range_values = self._parse_constraint_range(value_constraint)
            self._value_type_value_constraints[vt_id] = ORMValueTypeValueConstraint(vc_id, vt, range_values)

    def _parse_data_types(self):
        data_types = {}
        orm_data_types = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel", "orm:DataTypes")
        if orm_data_types:
            for k, v in orm_data_types.items():
                if v is not None:
                    data_types[v["@id"]] = k[4:]
        return data_types

    def _parse_roles(self):
        roles = {}
        ignored_roles = []
        orm_fact_types = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel", "orm:Facts", "orm:Fact")
        if orm_fact_types:
            for ft in self._single_object_to_list(orm_fact_types):
                relationship_name = ft['@_Name']
                unary_pattern = ft.get("@UnaryPattern", None)  # unary patterns are not supported
                orm_roles = self._get_nested(ft, "orm:FactRoles", "orm:Role")
                if orm_roles:
                    for ro in self._single_object_to_list(orm_roles):
                        role_id = ro["@id"]
                        role_name = ro["@Name"]
                        if (unary_pattern is not None and unary_pattern == "Negation") or role_id not in self._role_to_player.keys():
                            ignored_roles.append(role_id)
                        else:
                            roles[role_id] = ORMRole(role_id, role_name, relationship_name, self._role_to_player[role_id])
                            self._parse_role_cardinality_constraint(ro)
        return roles, ignored_roles

    def _parse_role_to_player_reference(self, object_type):
        roles = self._get_nested(object_type, "orm:PlayedRoles", "orm:Role")
        if roles:
            for role in self._single_object_to_list(roles):
                self._role_to_player[role["@ref"]] = object_type["@id"]

    def _parse_role_value_constraints(self):
        role_value_constraints = {}
        orm_fact_types = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel", "orm:Facts", "orm:Fact")
        if orm_fact_types:
            for ft in self._single_object_to_list(orm_fact_types):
                roles = self._get_nested(ft, "orm:FactRoles", "orm:Role")
                if roles and isinstance(roles, list):
                    for ro in roles:
                        role_id = ro.get("@id")
                        if role_id not in self._ignored_roles:
                            role_value_constraint = self._get_nested(ro, "orm:ValueRestriction", "orm:RoleValueConstraint")
                            if role_value_constraint:
                                range_values = self._parse_constraint_range(role_value_constraint)
                                role_value_constraints[role_id] = ORMRoleValueConstraint(self._roles[role_id], range_values)
        return role_value_constraints

    def _parse_constraint_range(self, orm_constraint_object):
        values = []
        value_range = self._get_nested(orm_constraint_object, "orm:ValueRanges", "orm:ValueRange")
        if value_range:
            for rvc in self._single_object_to_list(value_range):
                min_value = rvc.get("@MinValue")
                max_value = rvc.get("@MaxValue")
                if min_value and max_value:
                    if min_value == max_value:
                        values.append(min_value)
                    else:
                        values.append(ORMRange(min_value, max_value))
                else:
                    raise ValueError("Range value must have both MinValue and MaxValue defined.")
        return values

    def _parse_inclusive_role_constraints(self):
        constraints = []
        for ec in self._inclusion_constraints.values():
            if ec.roles and set(ec.roles).issubset(self._roles) and all(ro not in self._ignored_roles for ro in ec.roles):
                constraints.append(ORMInclusiveRoleConstraint(ec.id, ec.roles))
        return constraints

    def _parse_exclusive_role_constraints(self):
        constraints = []
        for ec in self._exclusion_constraints.values():
            flat_roles = [role for role_list in ec.roles for role in role_list]
            if ec.roles and set(flat_roles).issubset(self._roles) and all(ro not in self._ignored_roles for ro in flat_roles):
                constraints.append(ORMExclusiveRoleConstraint(ec.id, ec.roles))
        return constraints

    def _parse_subtype_facts(self):
        subtype_of = defaultdict(list)
        for subtype_arrow in self._parse_subtype_arrows():
            subtype_object = self._build_subtype_object(subtype_arrow)
            subtype_of[subtype_object.supertype_name].append(subtype_object)
        return subtype_of

    def _parse_subtype_arrows(self):
        subtype_of = []
        orm_subtype_facts = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                             "orm:Facts", "orm:SubtypeFact")
        if orm_subtype_facts:
            for sft in self._single_object_to_list(orm_subtype_facts):
                subtype_of.append(self._parse_subtype_arrow(sft))
        return subtype_of

    def _parse_subtype_arrow(self, subtype_fact):
        fact_roles = subtype_fact["orm:FactRoles"]
        subtype_id = self._get_nested(fact_roles, "orm:SubtypeMetaRole", "@id")
        subtype = self._get_nested(fact_roles, "orm:SubtypeMetaRole", "orm:RolePlayer", "@ref")
        supertype_id = self._get_nested(fact_roles, "orm:SupertypeMetaRole", "@id")
        supertype = self._get_nested(fact_roles, "orm:SupertypeMetaRole", "orm:RolePlayer", "@ref")
        return ORMSubtypeFact(subtype_id, subtype, supertype_id, supertype)

    def _parse_uniqueness_constraints(self):
        internal = {}
        external = {}
        orm_ucs = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                   "orm:Constraints", "orm:UniquenessConstraint")
        if orm_ucs:
            for uc in self._single_object_to_list(orm_ucs):
                uc_id = uc["@id"]
                pid = uc.get("orm:PreferredIdentifierFor", None)
                identifies = None
                if pid is not None and pid["@ref"] in self._entity_types:
                    identifies = pid["@ref"]
                roles = self._parse_role_sequence(uc)
                if roles:
                    target = internal if uc.get("@IsInternal") == "true" else external
                    target[uc_id] = ORMUniquenessConstraint(uc_id, roles, identifies)
        return internal, external

    def _process_internal_uniqueness_constraints(self):
        unique_roles = []
        fact_type_to_internal_uc = defaultdict(list)
        fact_type_to_complex_uc = defaultdict(list)
        identifier_fact_type_to_entity_type = defaultdict()

        for uc in self._internal_uniqueness_constraints.values():
            if uc.identifies is None and len(uc.roles) == 1:
                unique_roles.extend(uc.roles)

            role_id = uc.roles[0]
            role = self._roles.get(role_id)
            if not role or not role.relationship_name:
                continue

            fact_type = role.relationship_name

            fact_type_to_internal_uc[fact_type].append(uc)

            if uc.identifies is None:
                if len(uc.roles) > 1:
                    fact_type_to_complex_uc[fact_type].append(uc)
            else:
                identifier_fact_type_to_entity_type[fact_type] = self._entity_types[uc.identifies]

        return unique_roles, fact_type_to_internal_uc, fact_type_to_complex_uc, identifier_fact_type_to_entity_type

    def _parse_mandatory_constraints(self):
        mandatory_constraints = {}
        orm_mcs = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                   "orm:Constraints", "orm:MandatoryConstraint")
        if orm_mcs:
            for mc in self._single_object_to_list(orm_mcs):
                mc_id = mc["@id"]
                if mc.get("@IsSimple", None) is not None:
                    roles = self._parse_role_sequence(mc)
                    if roles:
                        mandatory_constraints[mc_id] = ORMMandatoryConstraint(mc_id, roles)
        return mandatory_constraints

    def _parse_value_comparison_constraints(self):
        value_comparison_constraints = {}
        orm_vccs = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                    "orm:Constraints", "orm:ValueComparisonConstraint")
        if orm_vccs:
            for vcc in self._single_object_to_list(orm_vccs):
                vcc_id = vcc["@id"]
                vcc_op = vcc["@Operator"]
                roles = self._parse_role_sequence(vcc)
                if roles:
                    constraint = ORMValueComparisonConstraint(vcc_id, ORMValueComparisonOperator(vcc_op), roles)
                    value_comparison_constraints[vcc_id] = constraint
        return value_comparison_constraints

    def _parse_role_subset_constraints(self):
        return self._parse_role_sequence_constraints("orm:SubsetConstraint", ORMRoleSubsetConstraint)

    def _parse_equality_constraints(self):
        return self._parse_role_sequence_constraints("orm:EqualityConstraint", ORMEqualityConstraint)

    def _parse_role_sequence_constraints(self, json_name, constraint_type: type):
        role_sequence_constraints = {}
        orm_constraints = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                    "orm:Constraints", json_name)
        if orm_constraints:
            for role_sequence_constraint in self._single_object_to_list(orm_constraints):
                id = role_sequence_constraint["@id"]
                roles = self._parse_role_sequences(role_sequence_constraint)
                if roles:
                    role_sequence_constraints[id] = constraint_type(id, roles)
        return role_sequence_constraints

    def _parse_inclusion_constraints(self):
        inclusion_constraints = {}
        orm_mcs = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                   "orm:Constraints", "orm:MandatoryConstraint")
        if orm_mcs:
            for mc in self._single_object_to_list(orm_mcs):
                mc_id = mc["@id"]
                mc_name = mc["@Name"]
                if mc_name.startswith("InclusiveOrConstraint"):
                    exclusive = mc.get("orm:ExclusiveOrExclusionConstraint", None) is not None
                    roles = self._parse_role_sequence(mc)
                    if roles:
                        inclusion_constraints[mc_id] = ORMInclusionConstraint(mc_id, roles, exclusive)
        return inclusion_constraints

    def _parse_exclusion_constraints(self):
        exclusion_constraints = {}
        orm_mcs = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                   "orm:Constraints", "orm:ExclusionConstraint")
        if orm_mcs:
            for ec in self._single_object_to_list(orm_mcs):
                ec_id = ec["@id"]
                inclusive = ec.get("orm:ExclusiveOrMandatoryConstraint", None) is not None
                role_sequences = self._parse_role_sequences(ec)
                if role_sequences:
                    exclusion_constraints[ec_id] = ORMExclusionConstraint(ec_id, role_sequences, inclusive)
        return exclusion_constraints

    def _parse_ring_constraints(self):
        ring_constraints = {}
        orm_rcs = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                   "orm:Constraints", "orm:RingConstraint")
        if orm_rcs:
            for rc in self._single_object_to_list(orm_rcs):
                rc_id = rc["@id"]
                rc_type = rc["@Type"]
                roles = self._parse_role_sequence(rc)
                if roles:
                    ring_constraints[rc_id] = ORMRingConstraint(rc_id, roles, self._process_ring_constraint(rc_type))
        return ring_constraints

    def _parse_frequency_constraints(self):
        frequency_constraints = {}
        orm_fcs = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel",
                                   "orm:Constraints", "orm:FrequencyConstraint")
        if orm_fcs:
            for fc in self._single_object_to_list(orm_fcs):
                fc_id = fc["@id"]
                min_freq = fc["@MinFrequency"]
                max_freq = fc["@MaxFrequency"]
                roles = self._parse_role_sequence(fc)
                if roles:
                    frequency_constraints[fc_id] = ORMFrequencyConstraint(fc_id, min_freq, max_freq, roles)
        return frequency_constraints

    def _parse_fact_types_reading_orders(self):
        fact_types_readings = defaultdict(list)
        fact_types = self._get_nested(self._ontology, "ormRoot:ORM2", "orm:ORMModel", "orm:Facts", "orm:Fact")
        if fact_types:
            for ft in self._single_object_to_list(fact_types):
                relationship_name = (ft['@_Name'])
                reading_orders = self._get_nested(ft, "orm:ReadingOrders", "orm:ReadingOrder")
                if reading_orders:
                    for ro in self._single_object_to_list(reading_orders):
                        reading_order = self._parse_fact_types_reading_order(ro)
                        if reading_order:
                            fact_types_readings[relationship_name].append(reading_order)
        return fact_types_readings

    def _parse_fact_types_reading_order(self, reading_order):
        results = []
        readings = self._get_nested(reading_order, "orm:Readings", "orm:Reading",)
        if readings:
            for rd in self._single_object_to_list(readings):
                expanded_data = self._get_nested(rd,  "orm:ExpandedData")
                if expanded_data:
                    front_text = expanded_data.get("@FrontText", None)
                    if front_text:
                        front_text = front_text.strip()

                    role_texts = self._get_nested(expanded_data,"orm:RoleText")
                    if role_texts:
                        # Step 1: Build roles with whatever RoleText exists
                        index_to_role = {}
                        for rt in self._single_object_to_list(role_texts):
                            index = int(rt["@RoleIndex"])
                            index_to_role[index] = ORMReadingRole(
                                index=index,
                                prefix=rt.get("@PreBoundText", "").strip() or None,
                                postfix=rt.get("@PostBoundText", "").strip() or None,
                                text=rt.get("@FollowingText", "").strip() or None,
                                role=None
                            )

                        # Step 2: Ensure all roles from RoleSequence are represented, even if no RoleText exists
                        roles = self._get_nested(reading_order, "orm:RoleSequence", "orm:Role")
                        if roles:
                            for i, role in enumerate(self._single_object_to_list(roles)):
                                role_id = role.get("@ref")
                                orm_role = self._roles.get(role_id, None)
                                if i in index_to_role:
                                    index_to_role[i].role = orm_role
                                else:
                                    # Fill in with None/defaults if RoleText is missing
                                    index_to_role[i] = ORMReadingRole(
                                        index=i,
                                        prefix=None,
                                        postfix=None,
                                        text=None,
                                        role=orm_role
                                    )
                        results.append(ORMReading(front_text, [index_to_role[i] for i in sorted(index_to_role)]))
        if len(results) > 1:
            warnings.warn("Multiple readings for the same reading order are not supported. Using the first one.")
        return results[0] if results else None

    def _parse_cardinality_constraint_range(self, cardinality_constraint):
        ranges = self._get_nested(cardinality_constraint, "orm:Ranges", "orm:CardinalityRange")
        # At least a range is always present within a cardinality constraint
        orm_ranges = []
        for rg in self._single_object_to_list(ranges):
            range_from = rg.get("@From")
            range_to = rg.get("@To")
            orm_ranges.append(ORMRange(range_from, range_to))
        return orm_ranges

    def _parse_cardinality_constraint(self, object_type):
        orm_cc = self._get_nested(object_type, "orm:CardinalityRestriction", "orm:CardinalityConstraint")
        if orm_cc:
            object_type_id = object_type.get("@id")
            cc_id = orm_cc.get("@id")
            ranges = self._parse_cardinality_constraint_range(orm_cc)
            self._cardinality_constraints[cc_id] = ORMCardinalityConstraint(cc_id, object_type_id, ranges)

    def _parse_role_cardinality_constraint(self, role):
        orm_rcc = self._get_nested(role, "orm:CardinalityRestriction", "orm:UnaryRoleCardinalityConstraint")
        if orm_rcc:
            role_id = role.get("@id")
            cc_id = orm_rcc.get("@id")
            ranges = self._parse_cardinality_constraint_range(orm_rcc)
            self._role_cardinality_constraints[role_id] = ORMRoleCardinalityConstraint(cc_id, role_id, ranges)

    @staticmethod
    def _get_nested(d, *keys):
        for key in keys:
            d = d.get(key)
            if d is None:
                return None
        return d

    def _build_subtype_object(self, subtype_arrow):
        sub_name = self._object_types[subtype_arrow.subtype].name
        sup_name = self._object_types[subtype_arrow.supertype].name
        # Look at exclusion constraints
        for ec_metadata in self._exclusion_constraints.values():
            flat_role_sequence = [role for role_list in ec_metadata.roles for role in role_list]
            if subtype_arrow.supertype_role_id in flat_role_sequence:
                if ec_metadata.inclusive:
                    return ExclusiveInclusiveSubtypeFact(sub_name, sup_name)
                else:
                    return ExclusiveSubtypeFact(sub_name, sup_name)
        # Look at inclusion constraints
        for ic_metadata in self._inclusion_constraints.values():
            if subtype_arrow.supertype_role_id in ic_metadata.roles:
                if ic_metadata.exclusive:
                    return ExclusiveInclusiveSubtypeFact(sub_name, sup_name)
                else:
                    return InclusiveSubtypeFact(sub_name, sup_name)
        # Default case, no constraints found
        return SubtypeFact(sub_name, sup_name)

    def _parse_mandatory_roles(self):
        mandatory_roles = []
        for mc in self._mandatory_constraints.values():
            mandatory_roles.extend(mc.roles)
        return mandatory_roles

    def _parse_role_sequences(self, orm_constraint):
        result = []
        role_sequences = self._get_nested(orm_constraint, "orm:RoleSequences", "orm:RoleSequence")
        if role_sequences:
            for rs in self._single_object_to_list(role_sequences):
                role_sequence = []
                roles = self._get_nested(rs, "orm:Role")
                if roles:
                    for ro in self._single_object_to_list(roles):
                        role_id = ro["@ref"]
                        # Ignore the entire constraint if it involves an ignored role
                        if role_id in self._ignored_roles:
                            return None
                        else:
                            role_sequence.append(role_id)
                    result.append(role_sequence)
        return result

    def _parse_role_sequence(self, orm_constraint):
        roles = self._get_nested(orm_constraint, "orm:RoleSequence", "orm:Role")
        role_sequence = []
        if roles:
            for ro in self._single_object_to_list(roles):
                role_id = ro["@ref"]
                # Ignore the entire constraint if it involves an ignored role
                if role_id in self._ignored_roles:
                    role_sequence = None
                    break
                else:
                    role_sequence.append(role_id)
        return role_sequence

    def _sort_subtype_facts(self):
        # Build a dependency graph to sort subtype facts so that child entity are declared
        # after the parent entity that they extend
        subtype_facts = self._subtype_facts
        edges = []
        nodes = ordered_set()
        sorted_subtype_facts = []
        # Parent depends on child, i.e., parent entity must be declared before child entity
        for parent in subtype_facts:
            nodes.add(parent)
            for child in subtype_facts[parent]:
                target = child.subtype_name
                edges.append((parent, target))
                nodes.add(target)
        for parent in topological_sort(list(nodes), edges):
            sorted_subtype_facts.extend(subtype_facts[parent])
        return sorted_subtype_facts

    @staticmethod
    def _process_ring_constraint(rc_type):
        pattern = '|'.join(r_type.value for r_type in ORMRingType)
        matches = re.finditer(pattern, rc_type)

        ring_types = []
        for match in matches:
            ring_types.append(ORMRingType(match.group(0)))
        return ring_types

    @staticmethod
    def _single_object_to_list(parsed_object):
        return parsed_object if isinstance(parsed_object, list) else [parsed_object]
