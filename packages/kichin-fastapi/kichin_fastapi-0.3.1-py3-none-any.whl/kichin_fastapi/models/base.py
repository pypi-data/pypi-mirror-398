"""Base resource model for all Kichin resources.

This module provides the BaseResourceModel class that serves as the foundation
for all resource types in Kichin. It includes file loading capabilities for
TOML, YAML, and JSON formats.
"""

import json
import tomllib
from pathlib import Path
from typing import Any, Generic, Self, TypeVar

import yaml
from pydantic import BaseModel, Field, computed_field

T = TypeVar("T", bound=BaseModel)

K = TypeVar("K", bound=str)


class BaseResourceModel[T, K](BaseModel):
    """Base model for all Kichin resource types.

    This generic base class provides common properties and file loading
    capabilities for all resource types in the Kichin system.

    Type Parameters:
        T: The type of the attributes field, must be a Pydantic BaseModel.

    Attributes:
        id: Unique identifier for the resource.
        name: Human-readable name of the resource.
        slug: URL-friendly identifier for the resource.
        kind: The type/kind of the resource (e.g., "Dataset", "Dashboard").
        attributes: Resource-specific attributes of type T.
    """

    id: str = Field(..., description="Unique identifier for the resource")
    name: str = Field(..., description="Human-friendly name of the resource")
    slug: str = Field(..., description="URL-friendly identifier for the resource")
    kind: K = Field(..., description="The type/kind of the resource")
    attributes: T = Field(..., description="Resource-specific attributes")

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> Self:
        """Load a resource from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            An instance of the resource model.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            pydantic.ValidationError: If the data doesn't match the model schema.
        """
        path = Path(file_path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)

    @classmethod
    def from_yaml_file(cls, file_path: str | Path) -> Self:
        """Load a resource from a YAML file.

        Args:
            file_path: Path to the YAML file.

        Returns:
            An instance of the resource model.

        Raises:
            FileNotFoundError: If the file does not exist.
            yaml.YAMLError: If the file contains invalid YAML.
            pydantic.ValidationError: If the data doesn't match the model schema.
        """
        path = Path(file_path)
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    @classmethod
    def from_toml_file(cls, file_path: str | Path) -> Self:
        """Load a resource from a TOML file.

        Args:
            file_path: Path to the TOML file.

        Returns:
            An instance of the resource model.

        Raises:
            FileNotFoundError: If the file does not exist.
            tomllib.TOMLDecodeError: If the file contains invalid TOML.
            pydantic.ValidationError: If the data doesn't match the model schema.
        """
        path = Path(file_path)
        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)

    @classmethod
    def from_file(cls, file_path: str | Path) -> Self:
        """Load a resource from a file, auto-detecting the format.

        The format is determined by the file extension:
        - .json: JSON format
        - .yaml, .yml: YAML format
        - .toml: TOML format

        Args:
            file_path: Path to the file.

        Returns:
            An instance of the resource model.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file extension is not supported.
            pydantic.ValidationError: If the data doesn't match the model schema.
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".json":
            return cls.from_json_file(path)
        elif suffix in {".yaml", ".yml"}:
            return cls.from_yaml_file(path)
        elif suffix == ".toml":
            return cls.from_toml_file(path)
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. Supported formats: .json, .yaml, .yml, .toml"
            )

    def _flatten(self, obj: Any) -> Any:
        """Recursively flatten a model, converting named lists to dicts.

        Args:
            obj: The object to flatten. Can be a BaseModel, list, or primitive.

        Returns:
            A flattened representation where lists of named items become dicts.
        """
        if isinstance(obj, BaseModel):
            result: dict[str, Any] = {}
            for field_name in type(obj).model_fields:
                result[field_name] = self._flatten(getattr(obj, field_name))
            return result
        elif isinstance(obj, list) and obj and hasattr(obj[0], "name"):
            return {item.name: self._flatten(item) for item in obj}
        elif isinstance(obj, list):
            return [self._flatten(item) for item in obj]
        return obj

    @computed_field
    @property
    def attributes_dict(self) -> dict[str, Any]:
        """Flatten attributes into nested dicts for O(1) lookups.

        Converts lists of items with 'name' attributes into dictionaries
        keyed by name, enabling fast access instead of O(n) list filtering.

        Example:
            # Instead of O(n) filtering:
            table = next((t for t in ds.attributes.tables if t.name == "orders"), None)
            dim = next((d for d in table.dimensions if d.name == "category"), None)

            # Use O(1) dict access:
            dim = ds.attributes_dict["tables"]["orders"]["dimensions"]["category"]

        Returns:
            A nested dictionary representation of the attributes.
        """
        return self._flatten(self.attributes)
