from dataclasses import dataclass, field
from typing import Hashable
import re

#------------------------------------------------------
# Naming helpers
#------------------------------------------------------


def sanitize(name:str) -> str:
    """ Cleanup the name to make it more palatable to names. """
    x = re.sub(r"[ ,\.\(\)\|\n]", "_", name)
    return x[0:-1] if x[-1] == "_" else x

#------------------------------------------------------
# Namer and NameCache
#------------------------------------------------------

@dataclass(frozen=True)
class Namer:
    """ Simple namer that keeps a single scope/context. """
    # in range mode, the first name will have a 0 suffix and the second will have a 1 suffix, etc.
    # otherwise, the first name will have no suffix, the second will have a _2 suffix, etc.
    range: bool = False
    next_count: dict[str, int] = field(default_factory=dict)

    def get_name(self, name: str) -> str:
        if name in self.next_count:
            c = self.next_count[name]
            self.next_count[name] = c + 1
            if self.range:
                new_name = f"{name}{c}"
            else:
                new_name = f"{name}_{c}"
            if new_name in self.next_count:
                # if the modified name is also in use, recurse
                return self.get_name(new_name)
            return new_name
        else:
            if self.range:
                self.next_count[name] = 1
                return f"{name}0"
            else:
                self.next_count[name] = 2
                return name

@dataclass
class NameCache:
    # support to generate object names with a count when there's collision
    # the next count to use as a suffix for an object with this name
    name_next_count: dict[Hashable, dict[str, int]] = field(default_factory=dict)
    # cache of the precomputed name for the object with this key
    name_cache: dict[Hashable, str] =  field(default_factory=dict)
    # whether to use _ or not
    use_underscore: bool = True
    # whether the first entry should start with a 1 or with nothing
    start_from_one: bool = False

    def get_name(self, key: Hashable, name: str, prefix: str = "") -> str:
        """
        Generate a unique name for the given key and base name, avoiding name collisions.

        Names are tracked and deduplicated using an internal counter. If a name has already
        been generated for the given key, the cached name is returned.

        For tuple keys (e.g., (relation_id, var_id)), the first element is used as the scope
        for counting name collisions. Only tuples of length 2 are supported; an assertion will
        fail otherwise.

        Parameters:
            key (Hashable): A unique key identifying the object. Can be an int or a (scope_id, local_id) tuple.
            name (str): Base name to use.
            prefix (str): Optional prefix to prepend to the name.

        Returns:
            str: A unique name string for the given key.

        Examples:
            # Global naming
            get_name(1, "var")           => "var"
            get_name(2, "var")           => "var_2"
            get_name(3, "var")           => "var_3"

            # Scoped naming (e.g., per relation)
            get_name((10, 1), "x")       => "x"
            get_name((10, 2), "x")       => "x_2"
            get_name((20, 1), "x")       => "x"     # Different scope, starts again
            get_name((20, 2), "x")       => "x_2"

            # With prefix and custom suffix start
            n = NameCache()
            n.get_name(1, "val", prefix="t_")                => "t_val"

            n = NameCache(start_from_one=True)
            n.get_name(1, "val", prefix="t_")                => "t_val_1"
        """
        if key in self.name_cache:
            return self.name_cache[key]

        # Derive the count scope from the key
        scope = None
        if isinstance(key, tuple):
            assert len(key) == 2, f"Expected tuple key of length 2, got {len(key)}: {key}"
            scope = key[0]  # e.g., relation_id

        # get the dict specific for the scope, or create one
        if scope in self.name_next_count:
            next_count = self.name_next_count[scope]
        else:
            next_count = dict()
            self.name_next_count[scope] = next_count

        # find the next available name
        name = self._find_next(f"{prefix}{name}", next_count)

        # register it for the key
        self.name_cache[key] = name
        return name

    def _find_next(self, name: str, next_count: dict):
        if name in next_count:
            # name is already in use, so append the next count
            c = next_count[name]
            next_count[name] = c + 1
            new_name = self._concat(name, c)

        else:
            # name not in use yet, so register it
            next_count[name] = 2
            if self.start_from_one:
                new_name = self._concat(name, 1)
            else:
                new_name = name

        if new_name != name:
            if new_name in next_count:
                # if the modified name is also in use, recurse
                return self._find_next(name, next_count)
            else:
                # otherwise, record that the modified name was used
                next_count[new_name] = 2
        return new_name

    def _concat(self, name: str, c: int):
        return f"{name}_{c}" if self.use_underscore else f"{name}{c}"
