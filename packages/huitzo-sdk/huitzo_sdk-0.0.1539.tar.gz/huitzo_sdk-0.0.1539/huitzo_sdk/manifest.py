"""
Manifest parser for Intelligence Pack huitzo.yaml files.

This module provides utilities for loading, parsing, and validating
huitzo.yaml manifest files that define Intelligence Pack metadata,
permissions, commands, data types, and service requirements.
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class PackInfo(BaseModel):
    """
    Basic pack metadata.

    Attributes:
        name: Pack name (e.g., "huitzo-plugin-duck")
        namespace: Command namespace (e.g., "duck")
        version: Semantic version (e.g., "1.0.0")
        visibility: Access control level (public, organization, private)
        description: Optional human-readable description
        author: Optional pack author/organization
        license: Optional license identifier
        homepage: Optional URL to pack homepage/docs
    """

    name: str = Field(..., min_length=1, description="Pack name")
    namespace: str = Field(..., min_length=1, description="Command namespace")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version")
    visibility: Literal["public", "organization", "private"] = Field(
        default="organization", description="Access control level"
    )
    description: str | None = Field(None, description="Pack description")
    author: str | None = Field(None, description="Pack author/organization")
    license: str | None = Field(None, description="License identifier")
    homepage: str | None = Field(None, description="Pack homepage URL")

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        """Validate namespace format (lowercase, no spaces)."""
        if not v.islower():
            raise ValueError("namespace must be lowercase")
        if " " in v or "/" in v:
            raise ValueError("namespace cannot contain spaces or slashes")
        return v


class CommandDef(BaseModel):
    """
    Command definition in manifest.

    Attributes:
        name: Command name (must match entry point name)
        description: Human-readable command description
        permissions: Required permissions/roles to execute
        deprecated: Whether command is deprecated
        hidden: Whether command should be hidden from listings
    """

    name: str = Field(..., min_length=1, description="Command name")
    description: str = Field(..., min_length=1, description="Command description")
    permissions: list[str] = Field(default_factory=list, description="Required permissions")
    deprecated: bool = Field(default=False, description="Is command deprecated")
    hidden: bool = Field(default=False, description="Hide from command listings")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate command name format."""
        if " " in v:
            raise ValueError("command name cannot contain spaces")
        return v


class DataTypeDef(BaseModel):
    """
    Data type definition for MongoDB storage.

    Attributes:
        name: Data type name (used in PluginDataStore)
        ttl_days: Optional TTL in days for automatic cleanup
        description: Optional description of data type
        indexed_fields: Optional list of fields to index
    """

    name: str = Field(..., min_length=1, description="Data type name")
    ttl_days: int | None = Field(None, gt=0, description="TTL in days")
    description: str | None = Field(None, description="Data type description")
    indexed_fields: list[str] = Field(
        default_factory=list, description="Fields to create indexes on"
    )


class ServiceRequirement(BaseModel):
    """
    Service dependency requirement.

    Attributes:
        name: Service name (llm, email, cron, etc.)
        required: Whether service is required or optional
        config: Optional service-specific configuration
    """

    name: str = Field(..., min_length=1, description="Service name")
    required: bool = Field(default=True, description="Is service required")
    config: dict[str, Any] = Field(default_factory=dict, description="Service configuration")


class DashboardConfig(BaseModel):
    """
    Dashboard configuration.

    Attributes:
        enabled: Whether dashboard is enabled
        subdomain: Dashboard subdomain (e.g., "duck" for /dashboards/duck/)
        version: Optional dashboard version (for versioned deployments)
        cdn_enabled: Whether CDN caching is enabled
    """

    enabled: bool = Field(default=False, description="Is dashboard enabled")
    subdomain: str | None = Field(None, description="Dashboard subdomain")
    version: str | None = Field(None, description="Dashboard version")
    cdn_enabled: bool = Field(default=True, description="Enable CDN caching")

    @field_validator("subdomain")
    @classmethod
    def validate_subdomain(cls, v: str | None) -> str | None:
        """Validate subdomain format."""
        if v is not None:
            if not v.islower():
                raise ValueError("subdomain must be lowercase")
            if " " in v or "/" in v:
                raise ValueError("subdomain cannot contain spaces or slashes")
        return v


class PackManifest(BaseModel):
    """
    Complete pack manifest structure.

    This represents the full huitzo.yaml file format.

    Attributes:
        pack: Pack metadata
        commands: List of command definitions
        data_types: Optional list of data type definitions
        services: Optional list of service requirements
        dashboard: Optional dashboard configuration
    """

    pack: PackInfo
    commands: list[CommandDef] = Field(..., min_length=1, description="Command definitions")
    data_types: list[DataTypeDef] | None = Field(None, description="Data type definitions")
    services: list[ServiceRequirement] | None = Field(None, description="Service requirements")
    dashboard: DashboardConfig | None = Field(None, description="Dashboard configuration")

    @property
    def command_names(self) -> set[str]:
        """Get set of all command names defined in manifest."""
        return {cmd.name for cmd in self.commands}

    @property
    def required_services(self) -> set[str]:
        """Get set of required service names."""
        if not self.services:
            return set()
        return {svc.name for svc in self.services if svc.required}

    @property
    def all_permissions(self) -> set[str]:
        """Get set of all permissions used across all commands."""
        permissions = set()
        for cmd in self.commands:
            permissions.update(cmd.permissions)
        return permissions


def load_manifest(manifest_path: Path | str) -> PackManifest:
    """
    Load and validate a huitzo.yaml manifest file.

    Args:
        manifest_path: Path to huitzo.yaml file

    Returns:
        Validated PackManifest instance

    Raises:
        FileNotFoundError: If manifest file doesn't exist
        yaml.YAMLError: If YAML is malformed
        pydantic.ValidationError: If manifest doesn't match schema

    Example:
        >>> manifest = load_manifest("huitzo.yaml")
        >>> print(manifest.pack.name)
        'huitzo-plugin-duck'
        >>> print(manifest.command_names)
        {'ask', 'history', 'clear'}
    """
    path = Path(manifest_path)

    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)

    if not isinstance(raw_data, dict):
        raise ValueError("Manifest must be a YAML dictionary")

    return PackManifest(**raw_data)


def validate_manifest(manifest: PackManifest) -> list[str]:
    """
    Validate manifest and return list of errors.

    Performs additional validation beyond Pydantic schema validation:
    - Dashboard subdomain matches namespace
    - No duplicate command names
    - No duplicate data type names
    - Service names are valid

    Args:
        manifest: Manifest to validate

    Returns:
        List of error messages (empty if valid)

    Example:
        >>> manifest = load_manifest("huitzo.yaml")
        >>> errors = validate_manifest(manifest)
        >>> if errors:
        ...     for error in errors:
        ...         print(f"ERROR: {error}")
    """
    errors: list[str] = []

    # Check for duplicate command names
    command_names = [cmd.name for cmd in manifest.commands]
    if len(command_names) != len(set(command_names)):
        duplicates = {name for name in command_names if command_names.count(name) > 1}
        errors.append(f"Duplicate command names: {duplicates}")

    # Check for duplicate data type names
    if manifest.data_types:
        data_type_names = [dt.name for dt in manifest.data_types]
        if len(data_type_names) != len(set(data_type_names)):
            duplicates = {name for name in data_type_names if data_type_names.count(name) > 1}
            errors.append(f"Duplicate data type names: {duplicates}")

    # Validate dashboard subdomain matches namespace (recommended)
    if manifest.dashboard and manifest.dashboard.enabled:
        if manifest.dashboard.subdomain and manifest.dashboard.subdomain != manifest.pack.namespace:
            errors.append(
                f"Dashboard subdomain '{manifest.dashboard.subdomain}' should match "
                f"pack namespace '{manifest.pack.namespace}' (recommended)"
            )

    # Validate service names (known services)
    known_services = {
        "llm",
        "email",
        "cron",
        "sites",
        "pdf",
        "qrcode",
        "telegram",
        "discord",
        "slack",
        "url_shortener",
        "validators",
        "formatters",
    }
    if manifest.services:
        for svc in manifest.services:
            if svc.name not in known_services:
                errors.append(
                    f"Unknown service '{svc.name}'. Known services: {sorted(known_services)}"
                )

    return errors


def validate_manifest_file(manifest_path: Path | str) -> tuple[PackManifest | None, list[str]]:
    """
    Load and validate a manifest file, returning both manifest and errors.

    This is a convenience function that combines load_manifest and validate_manifest.

    Args:
        manifest_path: Path to huitzo.yaml file

    Returns:
        Tuple of (manifest, errors). If loading fails, manifest is None.
        If validation succeeds, errors is empty list.

    Example:
        >>> manifest, errors = validate_manifest_file("huitzo.yaml")
        >>> if errors:
        ...     print(f"Validation failed: {errors}")
        ... else:
        ...     print(f"Manifest valid: {manifest.pack.name}")
    """
    try:
        manifest = load_manifest(manifest_path)
    except (FileNotFoundError, yaml.YAMLError, ValueError) as e:
        return None, [f"Failed to load manifest: {e}"]
    except Exception as e:
        return None, [f"Validation error: {e}"]

    errors = validate_manifest(manifest)
    return manifest, errors
