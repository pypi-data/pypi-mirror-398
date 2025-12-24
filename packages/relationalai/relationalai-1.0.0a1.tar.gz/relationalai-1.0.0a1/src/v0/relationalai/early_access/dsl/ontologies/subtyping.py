from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid
from v0.relationalai.semantics.metamodel.util import OrderedSet


class SubtypeArrow:
    start: Type
    end: Type

    def __init__(self, start: Type, end: Type):
        if end == start:
            raise Exception("Invalid subtype arrow. End can't be same as start.")
        self.start = start
        self.end = end

    def guid(self):
        return generate_stable_uuid(f"{self.start.guid()}->{self.end.guid()}")

    def pprint(self):
        return f"{self.start.display()}->{self.end.display()}"

    def to_name_tuple(self):
        return self.start.display(), self.end.display()

    def __eq__(self, other):
        if isinstance(other, SubtypeArrow):
            return self.guid() == other.guid()
        return False

    def __hash__(self):
        return hash(self.guid())

class SubtypeConstraint:
    arrows: OrderedSet[SubtypeArrow]

    def __init__(self, arrows: OrderedSet[SubtypeArrow]):
        if len(arrows) < 2:
            raise Exception("Invalid subtype constraint. Length of arrows is less than 2.")
        entity = next(iter(arrows))
        for arrow in arrows:
            if arrow is not entity and arrow.end != entity.end:
                raise Exception("Invalid subtype constraint. Subtype arrow end must be same for all arrows.")
        self.arrows = arrows


class ExclusiveSubtypeConstraint(SubtypeConstraint):

    def __init__(self, arrows: OrderedSet[SubtypeArrow]):
        super().__init__(arrows)


class InclusiveSubtypeConstraint(SubtypeConstraint):

    def __init__(self, arrows: OrderedSet[SubtypeArrow]):
        super().__init__(arrows)