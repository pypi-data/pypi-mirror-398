from __future__ import annotations
from pandas import DataFrame
from .errors import InvalidVersionKind, RAIInvalidVersionWarning
from packaging.version import Version
from typing import Dict, List, Optional, Tuple

# A simple container for 2 version objects, a lower bound and an upper bound, plus a version
# range string.
#
# Equivalent to a packaging SpecifierSet defined as ">={lower_bound}, <{upper_bound}", but
# has the benefit that we can check whether a version that is not contained by the set is
# lower than the lower bound or higher than the higher bound, which is important for error
# reporting.
# The vrange string is the Rel package manager representation of the low-high range. It
# differs from the python notation in that the upper bounds use wildcards and are inclusive
# (i.e. the range is <={upper bound}).
def version_range(low:str, high:str, vrange:str) -> tuple[Version, Version, str]:
    return (Version(low), Version(high), vrange)

# A list of rel libraries that the current version of relationalai depends on, including the
# range of compatible versions.
#
# NOTE: these dependencies are only verified if the use_package_manager option is enabled.
#
PACKAGE_DEPENDENCIES = [
    ('std', '24c1872c-de8a-5b12-7648-3d72f007a7a9', version_range('0.1.9', '0.2.0', '0.1.9 - 0.1.*'))
]

# Dependencies to libraries that are not packages, so we only check that their versions are
# compatible, but do not attempt to maintain them. Eventually this will be removed.
STATIC_DEPENDENCIES = [
    ('graphlib', '04cd9c07-16aa-4433-bdd7-adfdfaee317d', version_range('0.3.0', '0.4.0', '0.3.0 - 0.3.*')),
    ('std', '24c1872c-de8a-5b12-7648-3d72f007a7a9', version_range('0.1.5', '0.2.0', '0.1.5 - 0.1.*'))
]

#--------------------------------------------------
# Public API
#--------------------------------------------------

#
# Generate a Rel query that will lookup the versions of Rel libraries currently installed in
# the database, as well as whether the registry is up to date. This is used if the package
# manager is enabled.
#
def generate_query_package_manager():
    return _generate_query_package_manager(PACKAGE_DEPENDENCIES, STATIC_DEPENDENCIES)

#
# Generate a Rel query that will just check the static dependency versions. This is used if
# the package manager is not enabled.
#
def generate_query_version_check():
    # do not check package dependencies
    return _generate_query_version_check([], STATIC_DEPENDENCIES)

#
# Analyze packages in the database.
#
# This is similar to check_package_manager, but will only check the static dependencies.
# This is used when the package manager is not enabled.
#
def check_static_dependencies(
    installed_dependencies: Dict,
    platform: str,
    app_name: str,
    engine_name: str,
    model_name: str,
    warn_on_packages: bool = False
) -> None:
    _compare_dependencies(
        package_deps=[],
        static_deps=STATIC_DEPENDENCIES,
        installed_dependencies=installed_dependencies,
        platform=platform,
        app_name=app_name,
        engine_name=engine_name,
        model_name=model_name,
        warn_on_packages=warn_on_packages
    )

#
# Analyze the response of the "query_version_check" transaction.
#
# This is similar to check_package_manager_fallback, but will only check the static
# dependencies. This is used when the package manager is not enabled.
#
def check_static_dependencies_fallback(
    response: DataFrame,
    platform: str,
    app_name: str,
    engine_name: str,
    model_name: str,
    warn_on_packages: bool = False,
) -> None:
    results = response.results
    _compare_dependencies_fallback(
        [],
        STATIC_DEPENDENCIES,
        _extract_library_versions(results),
        _extract_std_version(results),
        platform,
        app_name,
        engine_name,
        model_name,
        warn_on_packages
    )

#
# Analyze the installed packages in the database.
#
# Return a tuple of booleans. The first boolean represents whether the registry is outdated
# and need to be updated. The second boolean represents whether the packages in the
# database are outdated and need to be updated.
#
# If `warn_on_packages` is set, also warn on outdated packages.
def check_package_manager(
    installed_dependencies: Dict,
    platform: str,
    app_name: str,
    engine_name: str,
    model_name: str,
    warn_on_packages: bool = False,
) -> Tuple[bool, bool]:
    update_packages, update_registry = _compare_dependencies(
        package_deps=PACKAGE_DEPENDENCIES,
        static_deps=STATIC_DEPENDENCIES,
        installed_dependencies=installed_dependencies,
        platform=platform,
        app_name=app_name,
        engine_name=engine_name,
        model_name=model_name,
        warn_on_packages=warn_on_packages
    )
    return update_registry, update_packages

#
# Analyze the response of the "query_package_manager" transaction.
#
# Return a tuple of booleans. The first boolean represents whether the registry is outdated
# and need to be updated. The second boolean represents whether the packages in the
# database are outdated and need to be updated.
#
# If `warn_on_packages` is set, also warn on outdated packages.
def check_package_manager_fallback(
    response: DataFrame,
    platform: str,
    app_name: str,
    engine_name: str,
    model_name: str,
    warn_on_packages: bool = False,
) -> Tuple[bool, bool]:
    results = response.results
    update_registry = _extract_update_registry(results)
    # if we need to update the registry, we also need to update packages
    if update_registry:
        return True, True

    update_packages = _compare_dependencies_fallback(
        PACKAGE_DEPENDENCIES,
        STATIC_DEPENDENCIES,
        _extract_library_versions(results),
        _extract_std_version(results),
        platform,
        app_name,
        engine_name,
        model_name,
        warn_on_packages
    )
    return False, update_packages

#
# Generate a Rel query to update the package registry, i.e. update the metadata to ensure
# the database is up to date with the available packages.
#
def generate_update_registry():
    return '''
    def response { ::std::pkg::registry::update_by_name["RAI"]}
    def insert { response[:insert] }
    def delete { response[:delete] }
    '''

#
# Generate a Rel query to update the package dependencies in the database to the latest
# available version.
#
def generate_update_packages():
    return _generate_update_packages(PACKAGE_DEPENDENCIES)

#--------------------------------------------------
# Implementation Details
#--------------------------------------------------

def _extract_update_registry(results):
    for result in results:
        if result["relationId"].startswith("/:output/:update_registry"):
            return True
    return False

def _extract_std_version(results):
    for result in results:
        if result["relationId"].startswith("/:output/:std"):
            for (version,) in result["table"].itertuples(index=False):
                return version
    return None

def _extract_library_versions(results):
    libraries = {}
    for result in results:
        if result["relationId"].startswith("/:output/:static_lock"):
            for (name, uuid, version) in result["table"].itertuples(index=False):
                libraries[(name, uuid)] = version
    return libraries

# Parse the package_versions coming from ERP metadata into the old format used by the
# fallback version check via the engine.
def _parse_package_versions_to_lock(package_versions: Dict[str, Dict[str, str]]) -> Dict[Tuple[str, str], str]:
    return {(version_dict["name"], uuid): version_dict["version"] for uuid, version_dict in package_versions.items()}

# Compare the current packages against the expected package_deps and static_deps. Raise
# warnings when necessary and return whether we should make the package manager update the
# package versions or even update the registry.
#
# Returns (update_packages, update_registry)
def _compare_dependencies(
        package_deps: List,
        static_deps: List,
        installed_dependencies: Dict,
        platform: str,
        app_name: str,
        engine_name: str,
        model_name: str,
        warn_on_packages: bool = False
    ) -> Tuple[bool, bool]:
    lock = _parse_package_versions_to_lock(installed_dependencies)

    # dependencies not yet kept in erp metadata. We need to fallback to retrieving package
    # version data from the engine directly.
    if not installed_dependencies:
        return True, True

    _warn_on_dependency_mismatch(
        package_deps=package_deps, 
        static_deps=static_deps, 
        lock=lock, 
        std=None,
        platform=platform, 
        app_name=app_name, 
        engine_name=engine_name, 
        model_name=model_name, 
        warn_on_packages=warn_on_packages,
    )

    # finally, check that all package dependencies are satisfied
    for (_, uuid, vrange) in package_deps:
        # library is missing from the database
        if uuid not in installed_dependencies:
            # currently, we do not know if the package is available in the registry, as the
            # ERP only stores information about install packages. So we need to update it to
            # make sure it exists
            return True, True

        version = Version(installed_dependencies[uuid]["version"])

        # version < vrange[0] -> Rel library version lower than lower bound, too old
        if version < vrange[0]:
            # if the installed version is too old, check if the fitting one is available
            # in the registry
            max_available_version = Version(installed_dependencies[uuid]["max_version"])
            if max_available_version < vrange[0]:
                return True, True
            return True, False

        # version >= vrange[1] -> Rel library version higher than upper bound, too new
        if version >= vrange[1]:
            return True, False

    # all dependencies satisfied
    return False, False

# Compare the current packages (in lock) and the value of std::version (in std) against the
# expected package_deps and static_deps. Raise warnings when necessary and return whether we
# should make the package manager update the package versions. This method is a fallback for
# when package metadata is not available in ERP and was instead retrieved by querying the
# engine. The engine response has a different structure than the ERP response, so we need to
# handle it differently.
def _compare_dependencies_fallback(
        package_deps: List,
        static_deps: List,
        lock: Dict,
        std: Optional[str],
        platform: str,
        app_name: str,
        engine_name: str,
        model_name: str,
        warn_on_packages = False,
    ) -> bool:
    _warn_on_dependency_mismatch(
        package_deps=package_deps, 
        static_deps=static_deps, 
        lock=lock, 
        std=std, 
        platform=platform, 
        app_name=app_name, 
        engine_name=engine_name, 
        model_name=model_name, 
        warn_on_packages=warn_on_packages,
    )

    # database is pre-versioning (before 0.1.0 was defined)
    if not lock and not std:
        return False

    # database is pre-package manager (between 0.1.0 and 0.1.5)
    if std:
        return False

    # finally, check that all package dependencies are satisfied
    for (name, uuid, vrange) in package_deps:
        key = (name, uuid)
        # library is missing from the database
        if key not in lock:
            return True

        version = Version(lock[key])
        # version >= vrange[1] -> Rel library version higher than upper bound, too new
        # version < vrange[0] -> Rel library version lower than lower bound, too old
        if version >= vrange[1] or version < vrange[0]:
            return True
    # all dependencies satisfied
    return False

# Check the static dependencies and potentially raise warnings. If `warn_on_packages` is
# set, also check and raise on package dependencies. Used for version checking without
# intent to upgrade.
def _warn_on_dependency_mismatch(
        package_deps: List,
        static_deps: List,
        lock: Dict,
        std: Optional[str],
        platform: str,
        app_name: str,
        engine_name: str,
        model_name: str,
        warn_on_packages = False,
    ) -> None:
    def warn(kind: InvalidVersionKind, expected, errors: list[tuple[InvalidVersionKind, str, str]] = []):
        RAIInvalidVersionWarning(
            kind=kind,
            expected=expected,
            lock=lock,
            platform=platform,
            app_name=app_name,
            engine_name=engine_name,
            model_name=model_name,
            errors=errors
        )
        return False

    # database is pre-versioning (before 0.1.0 was defined)
    if not lock and not std:
        warn(InvalidVersionKind.SchemaOutOfDate, static_deps)
        return

    # database is pre-package manager (between 0.1.0 and 0.1.5)
    if std:
        warn(InvalidVersionKind.SchemaOutOfDate, static_deps)
        return

    # database has a package manager, first, check the static dependencies and potentially
    # raise warnings
    # If `warn_on_packages` is set, also check and raise on package dependencies.
    # Used for version checking without intent to upgrade.
    deps_to_error_on = static_deps + package_deps if warn_on_packages else static_deps
    errors = []
    for (name, uuid, vrange) in deps_to_error_on:
        key = (name, uuid)
        # library is missing from the database
        if key not in lock:
            errors.append((InvalidVersionKind.SchemaOutOfDate, name, uuid))
        else:
            version = Version(lock[key])
            # Rel library version higher than upper bound, too new
            if version >= vrange[1]:
                errors.append((InvalidVersionKind.LibraryOutOfDate, name, uuid))

            # Rel library version lower than lower bound, too old
            if version < vrange[0]:
                errors.append((InvalidVersionKind.SchemaOutOfDate, name, uuid))

    if errors:
        if all(kind == InvalidVersionKind.LibraryOutOfDate for (kind, _, _) in errors):
            kind = InvalidVersionKind.LibraryOutOfDate
        elif all(kind == InvalidVersionKind.SchemaOutOfDate for (kind, _, _) in errors):
            kind = InvalidVersionKind.SchemaOutOfDate
        else:
            kind = InvalidVersionKind.Incompatible

        warn(kind, deps_to_error_on, errors)

def _generate_query_version_check(package_deps, static_deps):
    # deduplicate package entries
    checks = dict((name, uuid) for name, uuid, _ in package_deps)
    for name, uuid, _ in static_deps:
        if name not in checks:
            checks[name] = uuid

    static_lock_bindings = " ;\n            ".join(
        ["(\"%s\", \"%s\")" % (name, uuid) for name, uuid in checks.items()]
    )

    return f'''
    @no_diagnostics(:UNDEFINED_IDENTIFIER)
    def output[:std]: {{ std::version }}

    @no_diagnostics(:TYPE_MISMATCH)
    def output(:static_lock, name, uuid, version):
        rel(:pkg, :std, :pkg, :project, :static_lock, name, uuid, version) and
        {{
            {static_lock_bindings}
        }}(name, uuid)'''

def _generate_query_package_manager(package_deps, static_deps):
    lower_bounds = " ;\n        ".join(
        ["(\"%s\", \"%s\")" % (uuid, vrange[0]) for _, uuid, vrange in package_deps]
    )

    return f'''
    {_generate_query_version_check(package_deps, static_deps)}

    @no_diagnostics(:UNDEFINED_IDENTIFIER)
    def output[:update_registry]:
        exists((uuid, version) |
            lower_bounds(uuid, version) and
            not available(uuid, version) and
            ::std::pkg::registry::uuid(_, _)
        )

    def lower_bounds {{
        {lower_bounds}
    }}

    @no_diagnostics(:UNDEFINED_IDENTIFIER)
    @inline
    def available(uuid, version): {{
        exists((pkg, v, pv) |
            ::std::pkg::^Package(uuid_from_string[uuid], pkg) and
            ::std::pkg::^Version(version, v) and
            ::std::pkg::^PackageVersion(pkg, v, pv) and
            ::std::pkg::package_version::version(pv, v)
        )
    }}'''


def _generate_update_packages(package_deps):
    bindings = " ;\n        ".join(
        ["\"%s@%s\"" % (name, vrange[2]) for name, _, vrange in package_deps]
    )

    return f'''
    def response {{ ::std::pkg::project::update_package[{{
        {bindings}
    }}]}}
    def insert {{ response[:insert] }}
    def delete {{ response[:delete] }}
    '''
