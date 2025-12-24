from typing import List
from v0.relationalai.early_access.dsl.orm.models import Model, Relationship, Role
from v0.relationalai.early_access.dsl.orm.reasoners import Multiplicity

# Decapitalizes (lowers first character of) a string
def decapitalize(text: str) -> str: return text[:1].lower() + text[1:]

class Verbalizer:
    def __init__(self, model: Model):
        self._model = model

        # We cache incrementally maintainable RelationshipVerbaliers to prevent
        # unnecessary recalculation while users are actively editing a model.
        self._rel_verbs = {}

    def verbalize(self, rel: Relationship) -> str:
        if rel._id not in self._rel_verbs:
            self._rel_verbs[rel._id] = RelationshipVerbalizer(rel, self._model)
        return str(self._rel_verbs[rel._id])


# PointMultiplicityVerbalizers are used to verbalize constraints on the
# Roles of some Relationship using some specific RelationshipReading of
# that Relationship. We verbalize these constraints in the language of
# point multiplicities of a given Role
#
class PointMultiplicityVerbalizer:

    def __init__(self, reading, model: Model):
        self._model = model
        self._reading = reading

    # Use this reading to verbalize the multiplicity of *role* in a context
    # in which players for all of the other roles have been fixed.
    #
    def multiplicity_of(self, role: Role) -> str:
        arity = role._part_of()._arity()
        if arity == 1:
            return self._multiplicity_of_unary(role)
        if arity == 2:
            return self._multiplicity_of_binary(role)
        else:
            return self._multiplicity_of_nary(role)

    def sample_fact(self): return self._reading._sample_fact()

    # Binary relationships admit much more readable multiplicity verbalizations
    # than the more general n-ary relationships; so we handle them separately.
    #
    def _multiplicity_of_binary(self, role: Role):
        reading = self._reading

        role1_text = str(reading._role_in_reading[0])
        pos1_text = str(role1_text) if reading._follows[0] is None else str(role1_text) + " " + reading._follows[0]
        role2_text = str(reading._role_in_reading[1])
        pos2_text = role2_text if reading._follows[1] is None else str(role2_text) + " " + reading._follows[1]

        reasoner = self._model.reasoner()
        mult = reasoner.point_multiplicity(role)
        mult_verb = mult.qualifier()
        leads = reading._leading_text

        if role._id == reading._last()._id:
            # When the role with multiplicity is the second in this reading,
            # the reading is natural
            if mult.many():
                if leads is None:
                    return f"It is possible that some {pos1_text} {mult_verb} {pos2_text}"
                else:
                    return f"It is possible that {decapitalize(leads)} some {pos1_text} {mult_verb} {pos2_text}"
            else:
                if leads is None:
                    return f"Each {pos1_text} {mult_verb} {pos2_text}"
                else:
                    return f"{leads.capitalize()} each {pos1_text} {mult_verb} {pos2_text}"


        else:
            # The role with multiplicity is the first in this reading
            if mult.many():
                if leads is None:
                    return f"It is possible that for some {role2_text}, {mult_verb} {pos1_text} that {pos2_text}"
                else:
                    return f"It is possible that for some {role2_text}, {decapitalize(leads)} {mult_verb} {pos1_text} that {pos2_text}"
            else:
                if leads is None:
                    return f"For each {role2_text}, {mult_verb} {pos1_text} that {pos2_text}"
                else:
                    return f"For each {role2_text}, {decapitalize(leads)} {mult_verb} {pos1_text} that {pos2_text}"

    def _multiplicity_of_unary(self, role: Role) -> str:
        reading = self._reading
        point_variable = str(role.player())
        mult_verb = []
        if reading._leading_text is not None:
            mult_verb.append(decapitalize(reading._leading_text))
        mult_verb.append("that " + str(reading._role_in_reading[0]))
        follows = reading._follows[0]
        if follows is not None:
            mult_verb.append(reading._follows[0])

        return f"It is possible that for some {point_variable}, " + " ".join(mult_verb)

    def _multiplicity_of_nary(self, role: Role) -> str:

        def point_var_seq(pvars: List[str]) -> str:
            if len(pvars) == 1:
                return pvars[0]
            else:
                length = len(pvars) - 1
                return ", ".join(pvars[0:length]) + " and " + pvars[length]

        reading = self._reading

        point_variables = []
        mult_verb = []
        if reading._leading_text is not None:
            mult_verb.append(decapitalize(reading._leading_text))
        idx = 0
        role_verb = None
        for r in reading._roles():
            if role._id == r._id:
                qualifier = Multiplicity.qualifier(self._model.reasoner().point_multiplicity(role))
                role_verb = qualifier + " " + str(reading._role_in_reading[idx])
            else:
                role_verb = "that " + str(reading._role_in_reading[idx])
                point_variables.append(str(r.player()))
            follows = reading._follows[idx]
            if follows is None:
                mult_verb.append(role_verb)
            else:
                mult_verb.append(role_verb + " " + follows)
            idx += 1
    
        return "It is possible that for some " + point_var_seq(point_variables) + ", " + " ".join(mult_verb)


# RelationshipVerbalizers verbalize information about a Relationship in
# natural language, including a sample fact and a verbalization of its
# constraints in the form of a point multiplicity verbalization of each
# of its roles.
# 
# Generating good point multiplicity verbalizations is tricky because:
#   - the most natural way for a human to understand a point multiplicity
#     is when it is verbalized on the last role of some RelationshipReading,
#     but the model may not contain a reading in which a given role appears
#     last.
#   - mandatory and uniqueness constraints on the all of the Roles of the
#     Relationship can influence the point multiplicity of any given Role.
#  
class RelationshipVerbalizer:

    def __init__(self, relationship: Relationship, model: Model):
        self._relationship = relationship
        self._model = model

        # Number of readings of this relationship
        self._number_of_readings = 0   # Forces a sync with the model on first use

        # Maps the last role of a RelationshipReading to the PointMultiplicityVerbalizer
        #   for that reading. Used to simplify the choice of readings to use when
        #   verbalizing the point multiplicity of a Role, as the best ones are when
        #   the role appears last.
        self._role_to_verb = {}

        # Default verbalizer to use when verbalizing a point multiplicity of this
        #   Relationship when there is no better choice. Also used to verbalize
        #   sample facts of this Relationship because it is specific to a Reading.
        self._default_verb = None

    def __str__(self):
        default_reading = self.verbalizer_for()
        verb = [default_reading.sample_fact()]
        for role in self._relationship._rel_roles.values():
            reading_verb = self.verbalizer_for(role)
            verb.append(reading_verb.multiplicity_of(role))
        return "\n".join(verb)

    # Returns a verbalizer that is good for verbalizing the point multiplicity
    # of a given role of this Relationship. If no role is provided, returns
    # a default verbalizer.
    def verbalizer_for(self, role=None) -> PointMultiplicityVerbalizer:
        num_readings = len(self._relationship._readings)
        if self._number_of_readings < num_readings:
            # Then update the reading verbalizations to include those of any
            # newly added RelationshipReadings.
            #
            self._number_of_readings = num_readings
            self._role_to_verb = {}

            for reading in self._relationship._readings:
                reading_verb = PointMultiplicityVerbalizer(reading, self._model)
                self._role_to_verb[reading._last()._id] = reading_verb
                if self._default_verb is None:
                    self._default_verb = reading_verb

        if self._default_verb is None:
            raise Exception(f"Could not find a default reading for Relationship {self._relationship}")

        if role is not None and role._id in self._role_to_verb:
            return self._role_to_verb[role._id]
        
        # Otherwise choose an arbitary reading verbalization
        return self._default_verb