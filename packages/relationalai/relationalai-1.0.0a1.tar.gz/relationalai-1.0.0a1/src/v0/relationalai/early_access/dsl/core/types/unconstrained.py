from v0.relationalai.early_access.dsl.core.types import AbstractValueType
from v0.relationalai.early_access.dsl.core.types.variables import BasicTypeVariable
import numbers

class UnconstrainedValueType(AbstractValueType):

    def __init__(self, nm):
        AbstractValueType.__init__(self, nm)

    # Returns True if the Python constant `val` is an instance of this ValueType
    def contains(self, val) -> bool:
        if isinstance(val, numbers.Number):
            return self.basic_numeric()
        elif isinstance(val, str):
            return not self.basic_numeric()
        else:
            return False

    def pprint(self): return self.display()

    def ranges_over(self): return BasicTypeVariable(self)

    def relational(self): return False

    def root_unconstrained_type(self): return self

    def unconstrained(self): return True

class UnconstrainedNumericType(UnconstrainedValueType):

    def __init__(self, nm):
        UnconstrainedValueType.__init__(self, nm)

    def boolean(self): return self.display() == 'Boolean'

    # For verification purposes, we treat floats ad decimals. While not generally
    # safe, this is likely fine for constraints we will see in enterprise contexts.
    #
    def decimal(self): return self.display() == 'Decimal' or self.display() == 'Float'

    def integer(self): return self.display() == 'Integer' or self.display() == 'BigInteger'

    def basic_numeric(self) -> bool: return True

class UnsupportedUnconstrainedValueType(UnconstrainedValueType):
    def __init__(self, nm):
        UnconstrainedValueType.__init__(self, nm)

    def root_unconstrained_type(self):
        raise Exception(f"Unsupported basic type {self.display()} cannot be the base type of any value type")
