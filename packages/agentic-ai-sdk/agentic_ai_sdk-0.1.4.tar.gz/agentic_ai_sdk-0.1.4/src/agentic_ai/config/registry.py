"""Tool config registry for schema validation and injection.

This registry lets toolsets register their own config schemas, which are
loaded from env.yaml alongside BaseAppConfig without requiring AppConfig
aggregation.

Schema Resolution Strategy:
1. Config Class declares CONFIG_SECTION class variable (recommended)
2. Simple convention: ClassName -> remove "Config" suffix -> snake_case
3. Schema-less fallback (returns raw dict)

Example:
    class OpenMetadataConfig(BaseModel):
        CONFIG_SECTION: ClassVar[str] = "openmetadata"
        base_url: str
        token: str
"""
from __future__ import annotations

import importlib
import logging
import re
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from .base import ConfigError

LOGGER = logging.getLogger("agentic_ai.tool_config_registry")


def _to_snake_case(pascal_str: str) -> str:
    """Convert PascalCase to snake_case.
    
    Examples:
        "OpenMetadataConfig" -> "open_metadata_config"
        "AzureSearch" -> "azure_search"
    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', pascal_str).lower()


def _get_section_name_for_config(config_class: Type[BaseModel]) -> str:
    """Get the section name for a Config class.
    
    Strategy:
    1. Use CONFIG_SECTION class variable if defined
    2. Simple convention: remove "Config" suffix and convert to snake_case
    """
    # 1. Check for explicit CONFIG_SECTION
    config_section = getattr(config_class, "CONFIG_SECTION", None)
    if config_section is not None:
        return config_section
    
    # 2. Simple convention: ClassName -> remove Config -> snake_case
    name = config_class.__name__
    if name.endswith("Config"):
        name = name[:-6]  # Remove "Config" suffix
    return _to_snake_case(name)


class ToolConfigRegistry:
    """Registry for tool config schemas keyed by config section name.
    
    Supports three modes of schema resolution:
    1. Explicit registration via register() or register_schema_path()
    2. Auto-registration from Config classes with CONFIG_SECTION
    3. Schema-less fallback (raw dict returned as-is)
    """

    def __init__(self) -> None:
        self._schemas: dict[str, Type[BaseModel]] = {}

    @property
    def schemas(self) -> dict[str, Type[BaseModel]]:
        return dict(self._schemas)

    def register(self, name: str, schema: Type[BaseModel]) -> None:
        if not name:
            raise ValueError("Tool config name must be non-empty")
        existing = self._schemas.get(name)
        if existing is not None:
            if existing is schema:
                return
            raise ValueError(
                f"Tool config '{name}' already registered with {existing.__name__}"
            )
        self._schemas[name] = schema
        LOGGER.debug("Registered tool config schema: %s -> %s", name, schema.__name__)

    def register_schema_path(self, name: str, schema_path: str) -> None:
        schema = _resolve_schema_path(schema_path)
        self.register(name, schema)

    def register_config_class(self, config_class: Type[BaseModel]) -> str:
        """Register a Config class using its CONFIG_SECTION or convention.
        
        Returns:
            The section name used for registration.
        """
        section_name = _get_section_name_for_config(config_class)
        self.register(section_name, config_class)
        return section_name

    def register_from_module(self, module_path: str) -> None:
        """Import a module and register all Config classes found.
        
        Looks for classes ending with "Config" that have CONFIG_SECTION defined.
        """
        try:
            module = importlib.import_module(module_path)
            for name in dir(module):
                if name.endswith("Config") and not name.startswith("_"):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, BaseModel):
                        if hasattr(obj, "CONFIG_SECTION"):
                            self.register_config_class(obj)
        except ImportError as exc:
            LOGGER.debug("Failed to import module %s: %s", module_path, exc)

    def get_schema(self, section_name: str) -> Type[BaseModel] | None:
        """Get registered schema for a section name.
        
        Returns:
            Schema class if registered, None for schema-less mode.
        """
        return self._schemas.get(section_name)

    def load_section(self, name: str, raw_data: dict[str, Any] | None) -> Any:
        """Load a single config section with schema validation or schema-less fallback.
        
        Args:
            name: Section name
            raw_data: Raw configuration data for this section
            
        Returns:
            Validated Pydantic model if schema found, raw dict otherwise.
        """
        if raw_data is None:
            return None
            
        schema = self.get_schema(name)
        if schema is not None:
            try:
                return schema.model_validate(raw_data)
            except ValidationError as exc:
                raise ConfigError(
                    f"Invalid tool config section '{name}': {exc}"
                ) from exc
        else:
            # Schema-less: return raw dict
            LOGGER.debug("No schema for '%s', using schema-less mode", name)
            return raw_data

    def load_from_raw(
        self,
        raw: dict[str, Any],
        section_names: set[str] | None = None,
    ) -> dict[str, Any]:
        """Validate and load tool config sections from raw YAML mapping.
        
        Args:
            raw: Raw YAML configuration mapping
            section_names: Optional set of section names to load. If None,
                          loads all sections that have registered schemas.
                          
        Returns:
            Dict of section name -> validated config (or raw dict for schema-less).
        """
        tool_configs: dict[str, Any] = {}
        
        # Determine which sections to process
        if section_names is not None:
            names_to_process = section_names
        else:
            # Legacy behavior: only process explicitly registered schemas
            names_to_process = set(self._schemas.keys())
        
        for name in names_to_process:
            if name not in raw:
                continue
            tool_configs[name] = self.load_section(name, raw.get(name))
        
        return tool_configs


_REGISTRY = ToolConfigRegistry()


def register_tool_config(name: str, schema: Type[BaseModel]) -> None:
    """Register a tool config schema in the global registry."""
    _REGISTRY.register(name, schema)


def register_tool_config_schema(name: str, schema_path: str) -> None:
    """Register a tool config schema from a dotted path (module:Class)."""
    _REGISTRY.register_schema_path(name, schema_path)


def register_tool_config_schemas(schemas: dict[str, str]) -> None:
    """Register multiple tool config schemas from dotted paths."""
    for name, schema_path in schemas.items():
        if schema_path:
            _REGISTRY.register_schema_path(name, schema_path)


def register_config_module(module_path: str) -> None:
    """Register all Config classes from a module in the global registry.
    
    Args:
        module_path: Config module path (e.g., "toolsets.sql.config")
    """
    _REGISTRY.register_from_module(module_path)


def get_tool_config_registry() -> ToolConfigRegistry:
    """Return the global tool config registry."""
    return _REGISTRY


def _resolve_schema_path(path: str) -> Type[BaseModel]:
    try:
        if ":" in path:
            module_path, attr_path = path.split(":", 1)
        else:
            module_path, attr_path = path.rsplit(".", 1)

        module = importlib.import_module(module_path)
        target = module
        for attr in attr_path.split("."):
            target = getattr(target, attr)

        if not isinstance(target, type) or not issubclass(target, BaseModel):
            raise ConfigError(f"Schema '{path}' is not a Pydantic BaseModel.")
        return target
    except ConfigError:
        raise
    except Exception as exc:
        raise ConfigError(f"Failed to import tool config schema '{path}': {exc}") from exc


__all__ = [
    "ToolConfigRegistry",
    "register_tool_config",
    "register_tool_config_schema",
    "register_tool_config_schemas",
    "register_config_module",
    "get_tool_config_registry",
]
