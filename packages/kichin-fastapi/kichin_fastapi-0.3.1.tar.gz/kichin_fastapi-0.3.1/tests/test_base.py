"""Tests for BaseResourceModel and its core functionality.

Tests cover the base resource model including file loading capabilities
and the attributes_dict computed field for O(1) lookups.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from kichin_fastapi.models import (
    BaseResourceModel,
    Dataset,
    DatasetAttributes,
    Dimension,
    Fact,
    Metric,
    Relationship,
    RelationshipColumn,
    Table,
    TimeDimension,
)

# =============================================================================
# BaseResourceModel Tests
# =============================================================================


class TestBaseResourceModel:
    """Tests for the BaseResourceModel base class."""

    def test_base_resource_model_is_generic(self) -> None:
        """Test that BaseResourceModel works with generic type parameter."""
        # Dataset is BaseResourceModel[DatasetAttributes]
        dataset = Dataset(
            id="ds-generic",
            name="Generic Test",
            slug="generic-test",
            attributes=DatasetAttributes(),
        )

        assert isinstance(dataset, BaseResourceModel)
        assert isinstance(dataset.attributes, DatasetAttributes)

    def test_base_resource_model_required_fields(self) -> None:
        """Test that BaseResourceModel enforces required fields."""
        with pytest.raises(ValidationError) as exc_info:
            Dataset(
                name="Missing ID",
                slug="missing-id",
                attributes=DatasetAttributes(),
            )

        assert "id" in str(exc_info.value)


# =============================================================================
# File Loading Tests
# =============================================================================


class TestFileLoading:
    """Tests for file loading functionality in BaseResourceModel."""

    @pytest.fixture
    def sample_dataset_data(self) -> dict:
        """Sample dataset data for file loading tests."""
        return {
            "id": "ds-file",
            "name": "File Test Dataset",
            "slug": "file-test",
            "kind": "Dataset",
            "attributes": {
                "description": "Test dataset for file loading",
                "tables": [
                    {
                        "name": "orders",
                        "base_table": ["DB", "SCHEMA", "ORDERS"],
                    }
                ],
            },
        }

    def test_from_json_file(self, sample_dataset_data: dict) -> None:
        """Test loading from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_json_file(f.name)
            assert dataset.id == "ds-file"
            assert dataset.name == "File Test Dataset"

            Path(f.name).unlink()

    def test_from_yaml_file(self, sample_dataset_data: dict) -> None:
        """Test loading from YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_yaml_file(f.name)
            assert dataset.id == "ds-file"

            Path(f.name).unlink()

    def test_from_toml_file(self) -> None:
        """Test loading from TOML file."""
        toml_content = """
id = "ds-toml"
name = "TOML Dataset"
slug = "toml-dataset"
kind = "Dataset"

[attributes]
description = "TOML test"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()

            dataset = Dataset.from_toml_file(f.name)
            assert dataset.id == "ds-toml"

            Path(f.name).unlink()

    def test_from_file_auto_detect(self, sample_dataset_data: dict) -> None:
        """Test auto-detection of file format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_file(f.name)
            assert dataset.id == "ds-file"

            Path(f.name).unlink()

    def test_from_file_unsupported_format(self) -> None:
        """Test error for unsupported file format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<dataset></dataset>")
            f.flush()

            with pytest.raises(ValueError) as exc_info:
                Dataset.from_file(f.name)

            assert "Unsupported file format" in str(exc_info.value)

            Path(f.name).unlink()


# =============================================================================
# Attributes Dict Tests
# =============================================================================


class TestAttributesDict:
    """Tests for the attributes_dict computed field."""

    def test_attributes_dict_flattens_tables(self) -> None:
        """Test that tables list is flattened to dict keyed by name."""
        dataset = Dataset(
            id="ds-001",
            name="Test Dataset",
            slug="test-dataset",
            attributes=DatasetAttributes(
                tables=[
                    Table(name="orders", base_table=["DB", "SCHEMA", "ORDERS"]),
                    Table(name="customers", base_table=["DB", "SCHEMA", "CUSTOMERS"]),
                ]
            ),
        )

        assert "tables" in dataset.attributes_dict
        assert "orders" in dataset.attributes_dict["tables"]
        assert "customers" in dataset.attributes_dict["tables"]
        assert dataset.attributes_dict["tables"]["orders"]["name"] == "orders"

    def test_attributes_dict_flattens_nested_dimensions(self) -> None:
        """Test that nested dimensions are flattened to dict."""
        dataset = Dataset(
            id="ds-001",
            name="Test Dataset",
            slug="test-dataset",
            attributes=DatasetAttributes(
                tables=[
                    Table(
                        name="orders",
                        base_table=["DB", "SCHEMA", "ORDERS"],
                        dimensions=[
                            Dimension(name="category", expr="category", data_type="TEXT"),
                            Dimension(name="region", expr="region", data_type="TEXT"),
                        ],
                    ),
                ]
            ),
        )

        # Access nested dimension via dict
        dims = dataset.attributes_dict["tables"]["orders"]["dimensions"]
        assert "category" in dims
        assert "region" in dims
        assert dims["category"]["name"] == "category"
        assert dims["category"]["data_type"] == "TEXT"

    def test_attributes_dict_deep_access(self) -> None:
        """Test O(1) deep access to nested structures."""
        dataset = Dataset(
            id="ds-001",
            name="Test Dataset",
            slug="test-dataset",
            attributes=DatasetAttributes(
                tables=[
                    Table(
                        name="sales",
                        base_table=["DB", "SCHEMA", "SALES"],
                        dimensions=[
                            Dimension(
                                name="product_category",
                                expr="category",
                                data_type="TEXT",
                                sample_values=["Electronics", "Clothing"],
                            ),
                        ],
                        facts=[
                            Fact(name="amount", expr="amount"),
                        ],
                        metrics=[
                            Metric(name="total_sales", expr="SUM(amount)"),
                        ],
                    ),
                ]
            ),
        )

        # Deep O(1) access
        dim = dataset.attributes_dict["tables"]["sales"]["dimensions"]["product_category"]
        assert dim["name"] == "product_category"
        assert dim["sample_values"] == ["Electronics", "Clothing"]

        fact = dataset.attributes_dict["tables"]["sales"]["facts"]["amount"]
        assert fact["name"] == "amount"

        metric = dataset.attributes_dict["tables"]["sales"]["metrics"]["total_sales"]
        assert metric["expr"] == "SUM(amount)"

    def test_attributes_dict_flattens_relationships(self) -> None:
        """Test that relationships are flattened to dict."""
        dataset = Dataset(
            id="ds-001",
            name="Test Dataset",
            slug="test-dataset",
            attributes=DatasetAttributes(
                relationships=[
                    Relationship(
                        name="orders_to_customers",
                        left_table="orders",
                        right_table="customers",
                        relationship_columns=[
                            RelationshipColumn(left_column="customer_id", right_column="id")
                        ],
                        relationship_type="MANY_TO_ONE",
                    ),
                ]
            ),
        )

        rels = dataset.attributes_dict["relationships"]
        assert "orders_to_customers" in rels
        assert rels["orders_to_customers"]["left_table"] == "orders"

    def test_attributes_dict_preserves_scalar_fields(self) -> None:
        """Test that scalar fields are preserved as-is."""
        dataset = Dataset(
            id="ds-001",
            name="Test Dataset",
            slug="test-dataset",
            attributes=DatasetAttributes(
                description="A test dataset",
            ),
        )

        assert dataset.attributes_dict["description"] == "A test dataset"

    def test_attributes_dict_empty_lists(self) -> None:
        """Test that empty lists remain as empty dicts or lists."""
        dataset = Dataset(
            id="ds-001",
            name="Test Dataset",
            slug="test-dataset",
            attributes=DatasetAttributes(),
        )

        # Empty lists should remain as empty lists (no items with 'name' to check)
        assert dataset.attributes_dict["tables"] == []
        assert dataset.attributes_dict["relationships"] == []

    def test_attributes_dict_lists_without_name(self) -> None:
        """Test that lists without 'name' attribute remain as lists."""
        dataset = Dataset(
            id="ds-001",
            name="Test Dataset",
            slug="test-dataset",
            attributes=DatasetAttributes(
                tables=[
                    Table(
                        name="orders",
                        base_table=["DB", "SCHEMA", "ORDERS"],
                        primary_key=["order_id", "line_id"],
                    ),
                ]
            ),
        )

        # primary_key is a list of strings (no 'name' attr), should stay as list
        pk = dataset.attributes_dict["tables"]["orders"]["primary_key"]
        assert isinstance(pk, list)
        assert pk == ["order_id", "line_id"]
