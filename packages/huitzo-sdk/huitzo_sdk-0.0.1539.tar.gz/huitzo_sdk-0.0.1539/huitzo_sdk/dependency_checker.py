"""
Dependency compatibility checker for Intelligence Packs.

This module provides utilities to check if an Intelligence Pack's dependencies
conflict with the backend's dependencies. Since packs run in the same Python
process as the backend, they must use compatible version ranges.
"""

import re
from typing import NamedTuple


class Requirement(NamedTuple):
    """
    Parsed requirement specification.

    Attributes:
        package: Package name (normalized to lowercase)
        operator: Version operator (==, >=, >, <=, <, !=, ~=, or None)
        version: Version string (or None if no version specified)
        raw: Original requirement string
    """

    package: str
    operator: str | None
    version: str | None
    raw: str

    def __str__(self) -> str:
        """String representation of requirement."""
        if self.operator and self.version:
            return f"{self.package}{self.operator}{self.version}"
        return self.package

    @property
    def is_pinned(self) -> bool:
        """Check if requirement uses exact version pinning (==)."""
        return self.operator == "=="

    @property
    def is_flexible(self) -> bool:
        """Check if requirement uses flexible version constraint (>=, ~=, etc.)."""
        return self.operator in (">=", ">", "~=") if self.operator else True


def parse_requirement(req: str) -> Requirement:
    """
    Parse a requirement string into components.

    Supports standard PEP 440 version specifiers:
    - package==1.0.0 (exact)
    - package>=1.0.0 (minimum)
    - package>=1.0.0,<2.0.0 (range)
    - package~=1.0.0 (compatible)
    - package (no version)

    Args:
        req: Requirement string (e.g., "requests>=2.28.0")

    Returns:
        Parsed Requirement tuple

    Example:
        >>> req = parse_requirement("requests>=2.28.0")
        >>> req.package
        'requests'
        >>> req.operator
        '>='
        >>> req.version
        '2.28.0'
    """
    req = req.strip()

    # Handle extras like "package[extra]>=1.0.0"
    if "[" in req:
        req = re.sub(r"\[.*?\]", "", req)

    # Pattern to match package name and version specifier
    # Matches: package (==|>=|>|<=|<|!=|~=) version
    pattern = r"^([a-zA-Z0-9_-]+)\s*(==|>=|>|<=|<|!=|~=)?\s*([\d.]+.*)?$"
    match = re.match(pattern, req)

    if not match:
        # If no match, assume it's just a package name
        package_pattern = r"^([a-zA-Z0-9_-]+)"
        pkg_match = re.match(package_pattern, req)
        if pkg_match:
            return Requirement(
                package=pkg_match.group(1).lower(), operator=None, version=None, raw=req
            )
        raise ValueError(f"Invalid requirement format: {req}")

    package, operator, version = match.groups()
    return Requirement(package=package.lower(), operator=operator, version=version, raw=req)


def parse_requirements(requirements: list[str]) -> dict[str, Requirement]:
    """
    Parse list of requirement strings into package -> Requirement mapping.

    Args:
        requirements: List of requirement strings

    Returns:
        Dictionary mapping package names to Requirement objects

    Example:
        >>> reqs = parse_requirements(["requests>=2.28.0", "pydantic>=2.0.0"])
        >>> reqs["requests"].operator
        '>='
    """
    parsed: dict[str, Requirement] = {}
    for req in requirements:
        req = req.strip()
        if not req or req.startswith("#"):
            continue
        try:
            parsed_req = parse_requirement(req)
            parsed[parsed_req.package] = parsed_req
        except ValueError:
            # Skip invalid requirements
            continue
    return parsed


def check_version_compatibility(pack_req: Requirement, backend_req: Requirement) -> str | None:
    """
    Check if two requirements for the same package are compatible.

    Args:
        pack_req: Pack's requirement
        backend_req: Backend's requirement

    Returns:
        Error message if incompatible, None if compatible

    Compatibility Rules:
    1. If backend uses == (exact pin), pack must use same version or flexible (>=)
    2. If pack uses == (exact pin), it likely conflicts with backend
    3. If both use >=, check if versions overlap reasonably

    Example:
        >>> pack = parse_requirement("requests==2.28.0")
        >>> backend = parse_requirement("requests>=2.30.0")
        >>> error = check_version_compatibility(pack, backend)
        >>> error
        'Pack pins requests==2.28.0 but backend requires requests>=2.30.0'
    """
    # If pack has no version constraint, it's always compatible
    if not pack_req.operator or not pack_req.version:
        return None

    # If backend has no version constraint, pack's constraint is fine
    if not backend_req.operator or not backend_req.version:
        return None

    # Case 1: Pack uses exact pin (==)
    if pack_req.is_pinned:
        if backend_req.is_pinned:
            # Both pinned - must be exact match
            if pack_req.version != backend_req.version:
                return (
                    f"Pack pins {pack_req.package}=={pack_req.version} "
                    f"but backend requires {backend_req.package}=={backend_req.version}"
                )
        else:
            # Pack pinned, backend flexible - likely incompatible
            return (
                f"Pack pins {pack_req.package}=={pack_req.version} "
                f"but backend requires {backend_req} (use >= instead of ==)"
            )

    # Case 2: Backend uses exact pin (==), pack uses >=
    if backend_req.is_pinned and pack_req.operator == ">=":
        # Check if pack's minimum is <= backend's pinned version
        # This is a simplified check - proper version comparison would use packaging.version
        pack_version_parts = pack_req.version.split(".")
        backend_version_parts = backend_req.version.split(".")

        try:
            # Simple numeric comparison (major.minor.patch)
            for i in range(min(len(pack_version_parts), len(backend_version_parts))):
                pack_part = int(pack_version_parts[i])
                backend_part = int(backend_version_parts[i])
                if pack_part > backend_part:
                    return (
                        f"Pack requires {pack_req} but backend pins {backend_req} "
                        f"(pack minimum is too high)"
                    )
                elif pack_part < backend_part:
                    break  # Pack minimum is lower, compatible
        except ValueError:
            # Non-numeric version parts, skip detailed check
            pass

    # Case 3: Both use >= - check if they're reasonably close
    if pack_req.operator == ">=" and backend_req.operator == ">=":
        # Allow if they're within same major version
        try:
            pack_major = int(pack_req.version.split(".")[0])
            backend_major = int(backend_req.version.split(".")[0])
            if abs(pack_major - backend_major) > 1:
                return (
                    f"Pack requires {pack_req} but backend requires {backend_req} "
                    f"(major version mismatch)"
                )
        except (ValueError, IndexError):
            # Can't parse versions, skip check
            pass

    return None


def check_dependency_conflicts(
    pack_requirements: list[str], backend_requirements: list[str]
) -> list[str]:
    """
    Check for dependency conflicts between pack and backend requirements.

    This function identifies conflicts where a pack's dependency requirements
    would conflict with the backend's requirements when installed in the same
    Python environment.

    Args:
        pack_requirements: Pack's requirements (from pyproject.toml)
        backend_requirements: Backend's requirements (from huitzo-core)

    Returns:
        List of conflict descriptions (empty if no conflicts)

    Example:
        >>> pack_reqs = ["requests==2.28.0", "pydantic>=2.0.0"]
        >>> backend_reqs = ["requests>=2.30.0", "pydantic>=2.5.0"]
        >>> conflicts = check_dependency_conflicts(pack_reqs, backend_reqs)
        >>> for conflict in conflicts:
        ...     print(conflict)
        Pack pins requests==2.28.0 but backend requires requests>=2.30.0
    """
    conflicts: list[str] = []

    # Parse both sets of requirements
    pack_deps = parse_requirements(pack_requirements)
    backend_deps = parse_requirements(backend_requirements)

    # Check each pack dependency against backend
    for package, pack_req in pack_deps.items():
        if package not in backend_deps:
            continue  # Pack has extra dependency, no conflict

        backend_req = backend_deps[package]
        conflict = check_version_compatibility(pack_req, backend_req)
        if conflict:
            conflicts.append(conflict)

    return conflicts


def suggest_requirement_fix(pack_req: Requirement, backend_req: Requirement) -> str | None:
    """
    Suggest a compatible requirement string for the pack.

    Args:
        pack_req: Pack's current requirement
        backend_req: Backend's requirement

    Returns:
        Suggested requirement string, or None if no fix available

    Example:
        >>> pack = parse_requirement("requests==2.28.0")
        >>> backend = parse_requirement("requests>=2.30.0")
        >>> suggest_requirement_fix(pack, backend)
        'requests>=2.28.0'
    """
    # If pack uses ==, suggest using >=
    if pack_req.is_pinned and pack_req.version:
        return f"{pack_req.package}>={pack_req.version}"

    # If backend is pinned and pack uses >=, suggest matching backend's version
    if backend_req.is_pinned and backend_req.version:
        if pack_req.operator == ">=" and pack_req.version:
            # Suggest using backend's minimum
            return f"{pack_req.package}>={backend_req.version}"

    return None


def validate_pack_dependencies(
    pack_requirements: list[str], backend_requirements: list[str]
) -> tuple[bool, list[str], list[str]]:
    """
    Validate pack dependencies and return detailed results.

    This is a comprehensive validation function that checks for conflicts
    and provides suggestions for fixes.

    Args:
        pack_requirements: Pack's requirements
        backend_requirements: Backend's requirements

    Returns:
        Tuple of (is_valid, conflicts, suggestions)
        - is_valid: True if no conflicts
        - conflicts: List of conflict messages
        - suggestions: List of suggested fixes

    Example:
        >>> pack_reqs = ["requests==2.28.0"]
        >>> backend_reqs = ["requests>=2.30.0"]
        >>> valid, conflicts, suggestions = validate_pack_dependencies(pack_reqs, backend_reqs)
        >>> print(valid)
        False
        >>> print(conflicts)
        ['Pack pins requests==2.28.0 but backend requires requests>=2.30.0']
        >>> print(suggestions)
        ['Change requests==2.28.0 to requests>=2.28.0']
    """
    conflicts = check_dependency_conflicts(pack_requirements, backend_requirements)
    suggestions: list[str] = []

    if conflicts:
        pack_deps = parse_requirements(pack_requirements)
        backend_deps = parse_requirements(backend_requirements)

        for package, pack_req in pack_deps.items():
            if package in backend_deps:
                backend_req = backend_deps[package]
                fix = suggest_requirement_fix(pack_req, backend_req)
                if fix:
                    suggestions.append(f"Change {pack_req.raw} to {fix}")

    return len(conflicts) == 0, conflicts, suggestions
