"""Comprehensive tests for Dataset model and related models.

Tests cover all forms of creating Dataset objects including direct instantiation,
from dictionaries, and loading from JSON, YAML, and TOML files.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from kichin_fastapi.models import (
    Dataset,
    DatasetAttributes,
    Dimension,
    Fact,
    Filter,
    Metric,
    Relationship,
    RelationshipColumn,
    Table,
    TimeDimension,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_dimension_data() -> dict:
    """Sample dimension data for testing."""
    return {
        "name": "product_category",
        "synonyms": ["category", "product type"],
        "description": "Product category classification",
        "expr": "product_category",
        "data_type": "TEXT",
        "unique": False,
        "sample_values": ["Electronics", "Clothing", "Food"],
        "is_enum": True,
    }


@pytest.fixture
def sample_fact_data() -> dict:
    """Sample fact data for testing."""
    return {
        "name": "total_revenue",
        "synonyms": ["revenue", "sales"],
        "description": "Total revenue from sales",
        "expr": "price * quantity",
        "data_type": "NUMBER",
        "sample_values": ["1000.00", "2500.50"],
    }


@pytest.fixture
def sample_time_dimension_data() -> dict:
    """Sample time dimension data for testing."""
    return {
        "name": "order_date",
        "synonyms": ["date", "transaction date"],
        "description": "Date when order was placed",
        "expr": "order_timestamp",
        "data_type": "TIMESTAMP",
        "unique": False,
        "sample_values": ["2024-01-15", "2024-02-20"],
    }


@pytest.fixture
def sample_filter_data() -> dict:
    """Sample filter data for testing."""
    return {
        "name": "active_products",
        "synonyms": ["in stock", "available"],
        "description": "Filter for active products only",
        "expr": "status = 'ACTIVE'",
    }


@pytest.fixture
def sample_base_table_data() -> list[str]:
    """Sample base table reference data for testing."""
    return ["ANALYTICS_DB", "PUBLIC", "SALES_FACT"]


@pytest.fixture
def sample_table_data(
    sample_dimension_data: dict,
    sample_fact_data: dict,
    sample_time_dimension_data: dict,
    sample_filter_data: dict,
    sample_base_table_data: list[str],
) -> dict:
    """Sample table data for testing."""
    return {
        "name": "sales",
        "description": "Sales transactions table",
        "base_table": sample_base_table_data,
        "dimensions": [sample_dimension_data],
        "facts": [sample_fact_data],
        "time_dimensions": [sample_time_dimension_data],
        "filters": [sample_filter_data],
    }


@pytest.fixture
def sample_dataset_data(sample_table_data: dict) -> dict:
    """Sample complete dataset data for testing."""
    return {
        "id": "ds-001",
        "name": "Sales Analytics Dataset",
        "slug": "sales-analytics",
        "kind": "Dataset",
        "attributes": {
            "description": "Comprehensive sales analytics semantic model",
            "tables": [sample_table_data],
        },
    }


@pytest.fixture
def minimal_dataset_data() -> dict:
    """Minimal dataset data with required fields only."""
    return {
        "id": "ds-minimal",
        "name": "Minimal Dataset",
        "slug": "minimal-dataset",
        "kind": "Dataset",
        "attributes": {},
    }


# =============================================================================
# Dimension Model Tests
# =============================================================================


class TestDimension:
    """Tests for the Dimension model."""

    def test_create_dimension_full(self, sample_dimension_data: dict) -> None:
        """Test creating a dimension with all fields."""
        dimension = Dimension(**sample_dimension_data)

        assert dimension.name == "product_category"
        assert dimension.synonyms == ["category", "product type"]
        assert dimension.description == "Product category classification"
        assert dimension.expr == "product_category"
        assert dimension.data_type == "TEXT"
        assert dimension.unique is False
        assert dimension.sample_values == ["Electronics", "Clothing", "Food"]
        assert dimension.is_enum is True

    def test_create_dimension_minimal(self) -> None:
        """Test creating a dimension with minimal required fields."""
        dimension = Dimension(
            name="simple_dim",
            expr="column_name",
            data_type="TEXT",
        )

        assert dimension.name == "simple_dim"
        assert dimension.expr == "column_name"
        assert dimension.data_type == "TEXT"
        assert dimension.synonyms == []
        assert dimension.description is None
        assert dimension.unique is False
        assert dimension.sample_values == []
        assert dimension.is_enum is False

    def test_dimension_valid_data_types(self) -> None:
        """Test all valid dimension data types."""
        valid_types = [
            "TEXT",
            "NUMBER",
            "BOOLEAN",
            "VARCHAR",
        ]

        for data_type in valid_types:
            dimension = Dimension(
                name=f"{data_type.lower()}_dim",
                expr="column",
                data_type=data_type,
            )
            assert dimension.data_type == data_type


# =============================================================================
# Fact Model Tests
# =============================================================================


class TestFact:
    """Tests for the Fact model."""

    def test_create_fact_full(self, sample_fact_data: dict) -> None:
        """Test creating a fact with all fields."""
        fact = Fact(**sample_fact_data)

        assert fact.name == "total_revenue"
        assert fact.synonyms == ["revenue", "sales"]
        assert fact.description == "Total revenue from sales"
        assert fact.expr == "price * quantity"
        assert fact.data_type == "NUMBER"
        assert fact.sample_values == ["1000.00", "2500.50"]

    def test_create_fact_minimal(self) -> None:
        """Test creating a fact with minimal required fields."""
        fact = Fact(
            name="simple_fact",
            expr="amount",
        )

        assert fact.name == "simple_fact"
        assert fact.expr == "amount"
        assert fact.data_type == "NUMBER"
        assert fact.synonyms == []
        assert fact.description is None
        assert fact.sample_values == []


# =============================================================================
# Metric Model Tests
# =============================================================================


class TestMetric:
    """Tests for the Metric model."""

    def test_create_metric_full(self) -> None:
        """Test creating a metric with all fields."""
        metric = Metric(
            name="total_revenue",
            synonyms=["revenue", "sales total"],
            description="Sum of all revenue",
            expr="SUM(price * quantity)",
        )

        assert metric.name == "total_revenue"
        assert metric.synonyms == ["revenue", "sales total"]
        assert metric.description == "Sum of all revenue"
        assert metric.expr == "SUM(price * quantity)"

    def test_create_metric_minimal(self) -> None:
        """Test creating a metric with minimal required fields."""
        metric = Metric(
            name="count_orders",
            expr="COUNT(*)",
        )

        assert metric.name == "count_orders"
        assert metric.expr == "COUNT(*)"
        assert metric.synonyms == []
        assert metric.description is None


# =============================================================================
# Relationship Model Tests
# =============================================================================


class TestRelationship:
    """Tests for the Relationship model."""

    def test_create_relationship_full(self) -> None:
        """Test creating a relationship with all fields."""
        relationship = Relationship(
            name="orders_to_customers",
            left_table="orders",
            right_table="customers",
            relationship_columns=[
                RelationshipColumn(
                    left_column="customer_id",
                    right_column="id",
                )
            ],
            join_type="LEFT_OUTER",
            relationship_type="MANY_TO_ONE",
        )

        assert relationship.name == "orders_to_customers"
        assert relationship.left_table == "orders"
        assert relationship.right_table == "customers"
        assert len(relationship.relationship_columns) == 1
        assert relationship.relationship_columns[0].left_column == "customer_id"
        assert relationship.join_type == "LEFT_OUTER"
        assert relationship.relationship_type == "MANY_TO_ONE"

    def test_create_relationship_minimal(self) -> None:
        """Test creating a relationship with minimal required fields."""
        relationship = Relationship(
            name="simple_join",
            left_table="table_a",
            right_table="table_b",
            relationship_columns=[RelationshipColumn(left_column="id", right_column="a_id")],
            relationship_type="MANY_TO_ONE",
        )

        assert relationship.name == "simple_join"
        assert relationship.join_type == "LEFT_OUTER"  # default
        assert relationship.relationship_type == "MANY_TO_ONE"


class TestRelationshipColumn:
    """Tests for the RelationshipColumn model."""

    def test_create_relationship_column(self) -> None:
        """Test creating a relationship column pair."""
        col = RelationshipColumn(
            left_column="order_id",
            right_column="id",
        )

        assert col.left_column == "order_id"
        assert col.right_column == "id"


# =============================================================================
# TimeDimension Data Type Tests
# =============================================================================


class TestTimeDimensionDataTypes:
    """Tests for TimeDimension data type validation."""

    def test_time_dimension_valid_data_types(self) -> None:
        """Test all valid time dimension data types."""
        valid_types = ["DATE", "TIMESTAMP", "NUMBER"]

        for data_type in valid_types:
            time_dim = TimeDimension(
                name=f"{data_type.lower()}_dim",
                expr="ts_column",
                data_type=data_type,
            )
            assert time_dim.data_type == data_type


# =============================================================================
# TimeDimension Model Tests
# =============================================================================


class TestTimeDimension:
    """Tests for the TimeDimension model."""

    def test_create_time_dimension_full(self, sample_time_dimension_data: dict) -> None:
        """Test creating a time dimension with all fields."""
        time_dim = TimeDimension(**sample_time_dimension_data)

        assert time_dim.name == "order_date"
        assert time_dim.synonyms == ["date", "transaction date"]
        assert time_dim.description == "Date when order was placed"
        assert time_dim.expr == "order_timestamp"
        assert time_dim.data_type == "TIMESTAMP"
        assert time_dim.unique is False
        assert time_dim.sample_values == ["2024-01-15", "2024-02-20"]

    def test_create_time_dimension_minimal(self) -> None:
        """Test creating a time dimension with minimal required fields."""
        time_dim = TimeDimension(
            name="created_at",
            expr="created_timestamp",
        )

        assert time_dim.name == "created_at"
        assert time_dim.expr == "created_timestamp"
        assert time_dim.data_type == "TIMESTAMP"
        assert time_dim.synonyms == []
        assert time_dim.description is None
        assert time_dim.unique is False
        assert time_dim.sample_values == []


# =============================================================================
# Filter Model Tests
# =============================================================================


class TestFilter:
    """Tests for the Filter model."""

    def test_create_filter_full(self, sample_filter_data: dict) -> None:
        """Test creating a filter with all fields."""
        filter_obj = Filter(**sample_filter_data)

        assert filter_obj.name == "active_products"
        assert filter_obj.synonyms == ["in stock", "available"]
        assert filter_obj.description == "Filter for active products only"
        assert filter_obj.expr == "status = 'ACTIVE'"

    def test_create_filter_minimal(self) -> None:
        """Test creating a filter with minimal required fields."""
        filter_obj = Filter(
            name="simple_filter",
            expr="is_deleted = FALSE",
        )

        assert filter_obj.name == "simple_filter"
        assert filter_obj.expr == "is_deleted = FALSE"
        assert filter_obj.synonyms == []
        assert filter_obj.description is None


# =============================================================================
# Table Model Tests
# =============================================================================


class TestTable:
    """Tests for the Table model."""

    def test_create_table_full(self, sample_table_data: dict) -> None:
        """Test creating a table with all fields."""
        table = Table(**sample_table_data)

        assert table.name == "sales"
        assert table.description == "Sales transactions table"
        assert table.base_table == ["ANALYTICS_DB", "PUBLIC", "SALES_FACT"]
        assert len(table.dimensions) == 1
        assert len(table.facts) == 1
        assert len(table.time_dimensions) == 1
        assert len(table.filters) == 1

    def test_create_table_minimal(self, sample_base_table_data: list[str]) -> None:
        """Test creating a table with minimal required fields."""
        table = Table(
            name="minimal_table",
            base_table=sample_base_table_data,
        )

        assert table.name == "minimal_table"
        assert table.description is None
        assert table.dimensions == []
        assert table.facts == []
        assert table.time_dimensions == []
        assert table.filters == []

    def test_table_with_nested_objects(self, sample_base_table_data: list[str]) -> None:
        """Test creating a table with nested Pydantic objects."""
        dimension = Dimension(name="dim1", expr="col1", data_type="TEXT")
        fact = Fact(name="fact1", expr="SUM(val)")
        time_dim = TimeDimension(name="time1", expr="ts")
        filter_obj = Filter(name="filter1", expr="active = TRUE")

        table = Table(
            name="nested_table",
            base_table=sample_base_table_data,
            dimensions=[dimension],
            facts=[fact],
            time_dimensions=[time_dim],
            filters=[filter_obj],
        )

        assert table.dimensions[0].name == "dim1"
        assert table.facts[0].name == "fact1"
        assert table.time_dimensions[0].name == "time1"
        assert table.filters[0].name == "filter1"


# =============================================================================
# DatasetAttributes Model Tests
# =============================================================================


class TestDatasetAttributes:
    """Tests for the DatasetAttributes model."""

    def test_create_attributes_full(self, sample_table_data: dict) -> None:
        """Test creating dataset attributes with all fields."""
        attributes = DatasetAttributes(
            description="Full description",
            tables=[sample_table_data],
        )

        assert attributes.description == "Full description"
        assert len(attributes.tables) == 1
        assert attributes.tables[0].name == "sales"

    def test_create_attributes_empty(self) -> None:
        """Test creating dataset attributes with defaults."""
        attributes = DatasetAttributes()

        assert attributes.description is None
        assert attributes.tables == []


# =============================================================================
# Dataset Model Tests - Direct Instantiation
# =============================================================================


class TestDatasetDirectInstantiation:
    """Tests for Dataset model direct instantiation."""

    def test_create_dataset_full(self, sample_dataset_data: dict) -> None:
        """Test creating a dataset with all fields from dict."""
        dataset = Dataset(**sample_dataset_data)

        assert dataset.id == "ds-001"
        assert dataset.name == "Sales Analytics Dataset"
        assert dataset.slug == "sales-analytics"
        assert dataset.kind == "Dataset"
        assert dataset.attributes.description == ("Comprehensive sales analytics semantic model")
        assert len(dataset.attributes.tables) == 1

    def test_create_dataset_minimal(self, minimal_dataset_data: dict) -> None:
        """Test creating a dataset with minimal required fields."""
        dataset = Dataset(**minimal_dataset_data)

        assert dataset.id == "ds-minimal"
        assert dataset.name == "Minimal Dataset"
        assert dataset.slug == "minimal-dataset"
        assert dataset.kind == "Dataset"
        assert dataset.attributes.tables == []

    def test_create_dataset_with_pydantic_objects(self, sample_base_table_data: list[str]) -> None:
        """Test creating a dataset with nested Pydantic objects."""
        table = Table(
            name="products",
            base_table=sample_base_table_data,
            dimensions=[Dimension(name="name", expr="name", data_type="TEXT")],
        )
        attributes = DatasetAttributes(
            description="Product dataset",
            tables=[table],
        )

        dataset = Dataset(
            id="ds-products",
            name="Products Dataset",
            slug="products",
            attributes=attributes,
        )

        assert dataset.id == "ds-products"
        assert dataset.attributes.tables[0].name == "products"
        assert dataset.attributes.tables[0].dimensions[0].name == "name"

    def test_dataset_default_kind(self) -> None:
        """Test that Dataset has default kind value."""
        dataset = Dataset(
            id="ds-test",
            name="Test Dataset",
            slug="test-dataset",
            attributes=DatasetAttributes(),
        )

        assert dataset.kind == "Dataset"

    def test_create_dataset_from_model_validate(self, sample_dataset_data: dict) -> None:
        """Test creating a dataset using model_validate."""
        dataset = Dataset.model_validate(sample_dataset_data)

        assert dataset.id == "ds-001"
        assert dataset.name == "Sales Analytics Dataset"


# =============================================================================
# Dataset Model Tests - JSON File Loading
# =============================================================================


class TestDatasetJsonFileLoading:
    """Tests for Dataset model loading from JSON files."""

    def test_load_dataset_from_json_file(self, sample_dataset_data: dict) -> None:
        """Test loading a dataset from a JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_json_file(f.name)

            assert dataset.id == "ds-001"
            assert dataset.name == "Sales Analytics Dataset"
            assert len(dataset.attributes.tables) == 1

            Path(f.name).unlink()

    def test_load_dataset_from_json_file_path_object(self, sample_dataset_data: dict) -> None:
        """Test loading a dataset from a JSON file using Path object."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_json_file(Path(f.name))

            assert dataset.id == "ds-001"

            Path(f.name).unlink()

    def test_load_dataset_from_json_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for non-existent JSON file."""
        with pytest.raises(FileNotFoundError):
            Dataset.from_json_file("/nonexistent/path/dataset.json")


# =============================================================================
# Dataset Model Tests - YAML File Loading
# =============================================================================


class TestDatasetYamlFileLoading:
    """Tests for Dataset model loading from YAML files."""

    def test_load_dataset_from_yaml_file(self, sample_dataset_data: dict) -> None:
        """Test loading a dataset from a YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_yaml_file(f.name)

            assert dataset.id == "ds-001"
            assert dataset.name == "Sales Analytics Dataset"
            assert len(dataset.attributes.tables) == 1

            Path(f.name).unlink()

    def test_load_dataset_from_yml_file(self, sample_dataset_data: dict) -> None:
        """Test loading a dataset from a .yml file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_yaml_file(f.name)

            assert dataset.id == "ds-001"

            Path(f.name).unlink()

    def test_load_dataset_from_yaml_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for non-existent YAML file."""
        with pytest.raises(FileNotFoundError):
            Dataset.from_yaml_file("/nonexistent/path/dataset.yaml")


# =============================================================================
# Dataset Model Tests - TOML File Loading
# =============================================================================


class TestDatasetTomlFileLoading:
    """Tests for Dataset model loading from TOML files."""

    def test_load_dataset_from_toml_file(self) -> None:
        """Test loading a dataset from a TOML file."""
        toml_content = """
id = "ds-toml"
name = "TOML Dataset"
slug = "toml-dataset"
kind = "Dataset"

[attributes]
description = "Dataset loaded from TOML"

[[attributes.tables]]
name = "orders"
description = "Orders table"
base_table = ["DB", "PUBLIC", "ORDERS"]

[[attributes.tables.dimensions]]
name = "order_id"
expr = "order_id"
data_type = "TEXT"
unique = true

[[attributes.tables.facts]]
name = "total"
expr = "amount"
data_type = "NUMBER"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()

            dataset = Dataset.from_toml_file(f.name)

            assert dataset.id == "ds-toml"
            assert dataset.name == "TOML Dataset"
            assert dataset.attributes.description == "Dataset loaded from TOML"
            assert len(dataset.attributes.tables) == 1
            assert dataset.attributes.tables[0].name == "orders"
            assert len(dataset.attributes.tables[0].dimensions) == 1
            assert len(dataset.attributes.tables[0].facts) == 1

            Path(f.name).unlink()

    def test_load_dataset_from_toml_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for non-existent TOML file."""
        with pytest.raises(FileNotFoundError):
            Dataset.from_toml_file("/nonexistent/path/dataset.toml")


# =============================================================================
# Dataset Model Tests - Auto-Detection File Loading
# =============================================================================


class TestDatasetAutoFileLoading:
    """Tests for Dataset model auto-detection file loading."""

    def test_from_file_json(self, sample_dataset_data: dict) -> None:
        """Test auto-detecting JSON format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_file(f.name)

            assert dataset.id == "ds-001"

            Path(f.name).unlink()

    def test_from_file_yaml(self, sample_dataset_data: dict) -> None:
        """Test auto-detecting YAML format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_file(f.name)

            assert dataset.id == "ds-001"

            Path(f.name).unlink()

    def test_from_file_yml(self, sample_dataset_data: dict) -> None:
        """Test auto-detecting .yml format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_file(f.name)

            assert dataset.id == "ds-001"

            Path(f.name).unlink()

    def test_from_file_toml(self) -> None:
        """Test auto-detecting TOML format."""
        toml_content = """
id = "ds-auto-toml"
name = "Auto TOML Dataset"
slug = "auto-toml"
kind = "Dataset"

[attributes]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()

            dataset = Dataset.from_file(f.name)

            assert dataset.id == "ds-auto-toml"

            Path(f.name).unlink()

    def test_from_file_unsupported_format(self) -> None:
        """Test that ValueError is raised for unsupported file format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<dataset></dataset>")
            f.flush()

            with pytest.raises(ValueError) as exc_info:
                Dataset.from_file(f.name)

            assert "Unsupported file format: .xml" in str(exc_info.value)

            Path(f.name).unlink()

    def test_from_file_case_insensitive_extension(self, sample_dataset_data: dict) -> None:
        """Test that file extension detection is case-insensitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".JSON", delete=False) as f:
            json.dump(sample_dataset_data, f)
            f.flush()

            dataset = Dataset.from_file(f.name)

            assert dataset.id == "ds-001"

            Path(f.name).unlink()


# =============================================================================
# Validation Error Tests
# =============================================================================


class TestValidationErrors:
    """Tests for validation error handling."""

    def test_dataset_missing_required_field(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Dataset(
                id="ds-incomplete",
                # Missing: name, slug, attributes
            )

    def test_dimension_missing_required_field(self) -> None:
        """Test that Dimension requires name, expr, and data_type."""
        with pytest.raises(ValidationError):
            Dimension(name="incomplete")  # Missing expr and data_type

    def test_fact_missing_required_field(self) -> None:
        """Test that Fact requires name and expr."""
        with pytest.raises(ValidationError):
            Fact(name="incomplete")  # Missing expr

    def test_metric_missing_required_field(self) -> None:
        """Test that Metric requires name and expr."""
        with pytest.raises(ValidationError):
            Metric(name="incomplete")  # Missing expr

    def test_invalid_dimension_data_type(self) -> None:
        """Test that invalid dimension data_type raises ValidationError."""
        with pytest.raises(ValidationError):
            Dimension(
                name="invalid_dim",
                expr="column",
                data_type="INVALID_TYPE",
            )

    def test_invalid_time_dimension_data_type(self) -> None:
        """Test that invalid time dimension data_type raises ValidationError."""
        with pytest.raises(ValidationError):
            TimeDimension(
                name="invalid_time",
                expr="ts",
                data_type="TEXT",  # TEXT is not valid for time dimensions
            )

    def test_invalid_json_in_file(self) -> None:
        """Test that invalid JSON raises appropriate error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            f.flush()

            with pytest.raises(json.JSONDecodeError):
                Dataset.from_json_file(f.name)

            Path(f.name).unlink()


# =============================================================================
# Serialization Tests
# =============================================================================


class TestSerialization:
    """Tests for model serialization."""

    def test_dataset_to_dict(self, sample_dataset_data: dict) -> None:
        """Test serializing dataset to dictionary."""
        dataset = Dataset(**sample_dataset_data)
        data = dataset.model_dump()

        assert data["id"] == "ds-001"
        assert data["name"] == "Sales Analytics Dataset"
        assert "attributes" in data
        assert "tables" in data["attributes"]

    def test_dataset_to_json(self, sample_dataset_data: dict) -> None:
        """Test serializing dataset to JSON string."""
        dataset = Dataset(**sample_dataset_data)
        json_str = dataset.model_dump_json()

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["id"] == "ds-001"

    def test_round_trip_json(self, sample_dataset_data: dict) -> None:
        """Test that JSON serialization is reversible."""
        original = Dataset(**sample_dataset_data)
        json_str = original.model_dump_json()
        restored = Dataset.model_validate_json(json_str)

        assert original.id == restored.id
        assert original.name == restored.name
        assert original.slug == restored.slug
        assert len(original.attributes.tables) == len(restored.attributes.tables)

    def test_base_table_as_list(self) -> None:
        """Test that base_table is stored as a list of strings."""
        table = Table(
            name="test_table",
            base_table=["DB", "SCHEMA", "TABLE"],
        )

        assert isinstance(table.base_table, list)
        assert ".".join(table.base_table) == "DB.SCHEMA.TABLE"


# =============================================================================
# Uniqueness Validation Tests
# =============================================================================


class TestUniquenessValidation:
    """Tests for uniqueness validation in Dataset and Table models."""

    def test_duplicate_table_names_raises_error(self) -> None:
        """Test that duplicate table names raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DatasetAttributes(
                tables=[
                    Table(name="orders", base_table=["DB", "SCHEMA", "ORDERS"]),
                    Table(name="orders", base_table=["DB", "SCHEMA", "ORDERS_V2"]),
                ]
            )

        assert "Duplicate table names" in str(exc_info.value)
        assert "orders" in str(exc_info.value)

    def test_unique_table_names_succeeds(self) -> None:
        """Test that unique table names are accepted."""
        tables = [
            Table(name="orders", base_table=["DB", "SCHEMA", "ORDERS"]),
            Table(name="customers", base_table=["DB", "SCHEMA", "CUSTOMERS"]),
        ]
        attrs = DatasetAttributes(tables=tables)

        assert len(attrs.tables) == len(tables)

    def test_duplicate_dimension_names_raises_error(self) -> None:
        """Test that duplicate dimension names raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Table(
                name="test_table",
                base_table=["DB", "SCHEMA", "TABLE"],
                dimensions=[
                    Dimension(name="category", expr="category", data_type="TEXT"),
                    Dimension(name="category", expr="category2", data_type="TEXT"),
                ],
            )

        assert "Duplicate column names" in str(exc_info.value)
        assert "category" in str(exc_info.value)

    def test_duplicate_across_column_types_raises_error(self) -> None:
        """Test that duplicate names across different column types raise error."""
        with pytest.raises(ValidationError) as exc_info:
            Table(
                name="test_table",
                base_table=["DB", "SCHEMA", "TABLE"],
                dimensions=[
                    Dimension(name="amount", expr="category", data_type="TEXT"),
                ],
                facts=[
                    Fact(name="amount", expr="amount"),
                ],
            )

        assert "Duplicate column names" in str(exc_info.value)
        assert "amount" in str(exc_info.value)

    def test_duplicate_time_dimension_and_metric_raises_error(self) -> None:
        """Test duplicate between time_dimension and metric raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Table(
                name="test_table",
                base_table=["DB", "SCHEMA", "TABLE"],
                time_dimensions=[
                    TimeDimension(name="created_at", expr="created_at"),
                ],
                metrics=[
                    Metric(name="created_at", expr="COUNT(*)"),
                ],
            )

        assert "Duplicate column names" in str(exc_info.value)
        assert "created_at" in str(exc_info.value)

    def test_unique_columns_across_types_succeeds(self) -> None:
        """Test that unique column names across all types are accepted."""
        table = Table(
            name="test_table",
            base_table=["DB", "SCHEMA", "TABLE"],
            dimensions=[
                Dimension(name="category", expr="category", data_type="TEXT"),
            ],
            time_dimensions=[
                TimeDimension(name="created_at", expr="created_at"),
            ],
            facts=[
                Fact(name="amount", expr="amount"),
            ],
            metrics=[
                Metric(name="total_amount", expr="SUM(amount)"),
            ],
        )

        assert len(table.dimensions) == 1
        assert len(table.time_dimensions) == 1
        assert len(table.facts) == 1
        assert len(table.metrics) == 1

    def test_multiple_duplicates_reported(self) -> None:
        """Test that all duplicate names are reported in error."""
        with pytest.raises(ValidationError) as exc_info:
            Table(
                name="test_table",
                base_table=["DB", "SCHEMA", "TABLE"],
                dimensions=[
                    Dimension(name="dup1", expr="col1", data_type="TEXT"),
                    Dimension(name="dup1", expr="col2", data_type="TEXT"),
                    Dimension(name="dup2", expr="col3", data_type="TEXT"),
                ],
                facts=[
                    Fact(name="dup2", expr="col4"),
                ],
            )

        error_msg = str(exc_info.value)
        assert "dup1" in error_msg
        assert "dup2" in error_msg

    def test_duplicate_relationship_names_raises_error(self) -> None:
        """Test that duplicate relationship names raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DatasetAttributes(
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
                    Relationship(
                        name="orders_to_customers",
                        left_table="orders",
                        right_table="products",
                        relationship_columns=[
                            RelationshipColumn(left_column="product_id", right_column="id")
                        ],
                        relationship_type="MANY_TO_ONE",
                    ),
                ]
            )

        assert "Duplicate relationship names" in str(exc_info.value)
        assert "orders_to_customers" in str(exc_info.value)

    def test_unique_relationship_names_succeeds(self) -> None:
        """Test that unique relationship names are accepted."""
        relationships = [
            Relationship(
                name="orders_to_customers",
                left_table="orders",
                right_table="customers",
                relationship_columns=[
                    RelationshipColumn(left_column="customer_id", right_column="id")
                ],
                relationship_type="MANY_TO_ONE",
            ),
            Relationship(
                name="orders_to_products",
                left_table="orders",
                right_table="products",
                relationship_columns=[
                    RelationshipColumn(left_column="product_id", right_column="id")
                ],
                relationship_type="MANY_TO_ONE",
            ),
        ]
        attrs = DatasetAttributes(relationships=relationships)

        assert len(attrs.relationships) == len(relationships)
