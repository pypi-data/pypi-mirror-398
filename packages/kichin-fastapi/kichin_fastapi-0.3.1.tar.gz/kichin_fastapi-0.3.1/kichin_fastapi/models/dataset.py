"""Dataset model for semantic data modeling.

This module provides the Dataset resource model and its child models for
representing semantic data models used in analytical queries.
"""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from kichin_fastapi.models.base import BaseResourceModel

type DimensionDataType = Literal[
    "TEXT",
    "NUMBER",
    "BOOLEAN",
    "VARCHAR",
]

type TimeDimensionDataType = Literal[
    "DATE",
    "TIMESTAMP",
    # can include NUMBER for epoch timestamps (unix timestamps)
    "NUMBER",
]

type FactDataType = Literal["NUMBER"]

type JoinType = Literal[
    "LEFT_OUTER",
    "INNER",
]

type RelationshipType = Literal[
    "MANY_TO_ONE",
    "ONE_TO_ONE",
]


class Dimension(BaseModel):
    """A dimension column in a semantic model table.

    Dimensions are categorical columns used for grouping, filtering,
    and slicing data in analytical queries.

    Attributes:
        name: Unique identifier for the dimension.
        synonyms: Alternative terms users might use.
        description: Data characteristics and business context.
        expr: SQL expression (can reference own table or other logical tables).
        data_type: Column data type.
        unique: Whether values in this dimension are unique.
        sample_values: Example values users might reference.
        is_enum: Whether this represents an exhaustive value list.
    """

    name: str = Field(
        ...,
        description="Unique identifier for the dimension",
    )
    synonyms: list[str] = Field(
        default_factory=list,
        description="Alternative terms users might use",
    )
    description: str | None = Field(
        default=None,
        description="Data characteristics and business context",
    )
    expr: str = Field(
        ...,
        description="SQL expression for the dimension",
    )
    data_type: DimensionDataType = Field(
        ...,
        description="Column data type",
    )
    unique: bool = Field(
        default=False,
        description="Whether values are unique",
    )
    sample_values: list[str] = Field(
        default_factory=list,
        description="Example values users might reference",
    )
    is_enum: bool = Field(
        default=False,
        description="Whether this is an exhaustive value list",
    )


class Fact(BaseModel):
    """A fact column in a semantic model table.

    Facts are quantitative, row-level values that can be aggregated.
    Note: Facts are raw values; use Metrics for aggregations.

    Attributes:
        name: Unique identifier for the fact.
        synonyms: Alternative terminology.
        description: Business meaning and calculation details.
        expr: SQL expression for the fact computation.
        data_type: Numeric or applicable type.
        sample_values: Representative examples.
    """

    name: str = Field(
        ...,
        description="Unique identifier for the fact",
    )
    synonyms: list[str] = Field(
        default_factory=list,
        description="Alternative terminology",
    )
    description: str | None = Field(
        default=None,
        description="Business meaning and calculation details",
    )
    expr: str = Field(
        ...,
        description="SQL expression for the fact",
    )
    data_type: FactDataType = Field(
        default="NUMBER",
        description="Data type",
    )
    sample_values: list[str] = Field(
        default_factory=list,
        description="Representative examples",
    )


class TimeDimension(BaseModel):
    """A time dimension column in a semantic model table.

    Time dimensions provide temporal context for analytical queries.

    Attributes:
        name: Unique identifier for the time dimension.
        synonyms: Alternative references.
        description: Temporal context (include timezone info for DATETIME).
        expr: SQL expression deriving the temporal value.
        data_type: DATE, TIMESTAMP, or NUMBER (for epoch timestamps).
        unique: Whether values are unique.
        sample_values: Relevant date/time examples.
    """

    name: str = Field(
        ...,
        description="Unique identifier for the time dimension",
    )
    synonyms: list[str] = Field(
        default_factory=list,
        description="Alternative references",
    )
    description: str | None = Field(
        default=None,
        description="Temporal context (include timezone for DATETIME)",
    )
    expr: str = Field(..., description="SQL expression for the time dimension")
    data_type: TimeDimensionDataType = Field(
        default="TIMESTAMP", description="DATE, TIMESTAMP, or NUMBER"
    )
    unique: bool = Field(default=False, description="Whether values are unique")
    sample_values: list[str] = Field(
        default_factory=list, description="Relevant date/time examples"
    )


class Filter(BaseModel):
    """A predefined filter condition in a semantic model table.

    Filters define reusable SQL conditions that reference logical columns.

    Attributes:
        name: Unique identifier for the filter.
        synonyms: Alternative terms.
        description: Use cases and filtering purpose.
        expr: SQL condition referencing logical columns.
    """

    name: str = Field(
        ...,
        description="Unique identifier for the filter",
    )
    synonyms: list[str] = Field(
        default_factory=list,
        description="Alternative terms",
    )
    description: str | None = Field(
        default=None,
        description="Use cases and filtering purpose",
    )
    expr: str = Field(
        ...,
        description="SQL condition referencing logical columns",
    )


class Metric(BaseModel):
    """An aggregated measure in a semantic model.

    Metrics are aggregate SQL expressions (SUM, AVG, etc.) over facts/dimensions.
    Unlike facts (row-level), metrics represent aggregated calculations.

    Attributes:
        name: Unique identifier for the metric.
        synonyms: Alternative terminology.
        description: Business interpretation of the metric.
        expr: Aggregate SQL expression over facts/dimensions.
    """

    name: str = Field(
        ...,
        description="Unique identifier for the metric",
    )
    synonyms: list[str] = Field(
        default_factory=list,
        description="Alternative terminology",
    )
    description: str | None = Field(
        default=None,
        description="Business interpretation",
    )
    expr: str = Field(
        ...,
        description="Aggregate SQL expression",
    )


class RelationshipColumn(BaseModel):
    """A column pair for relationship joins.

    Attributes:
        left_column: Column from the left (source) table.
        right_column: Column from the right (target) table.
    """

    left_column: str = Field(
        ...,
        description="Column from the left table",
    )
    right_column: str = Field(
        ...,
        description="Column from the right table",
    )


class Relationship(BaseModel):
    """A join definition between tables in a semantic model.

    Relationships define how tables are connected for multi-table queries.

    Attributes:
        name: Unique identifier for the relationship.
        left_table: Source table name (many side for many-to-one).
        right_table: Target table name (one side for many-to-one).
        relationship_columns: Column pairs defining the join path.
        join_type: Type of join (left_outer or inner).
        relationship_type: Cardinality (many_to_one or one_to_one).
    """

    name: str = Field(
        ...,
        description="Unique identifier for the relationship",
    )
    left_table: str = Field(
        ...,
        description="Source table name",
    )
    right_table: str = Field(
        ...,
        description="Target table name",
    )
    relationship_columns: list[RelationshipColumn] = Field(
        ...,
        description="Column pairs for the join",
    )
    join_type: JoinType = Field(
        default="LEFT_OUTER",
        description="Type of join (LEFT_OUTER or INNER)",
    )
    relationship_type: RelationshipType = Field(
        ...,
        description="Relationship cardinality (many_to_one or one_to_one)",
    )


class Table(BaseModel):
    """A logical table in a semantic model.

    Tables map to physical database tables/views and contain dimensions,
    facts, time dimensions, metrics, and filters.

    Attributes:
        name: Unique identifier for the table.
        synonyms: Alternative terminology.
        description: Purpose and content details.
        base_table: Fully qualified reference to physical table.
        primary_key: Columns uniquely identifying rows (required for relationships).
        dimensions: Categorical columns.
        time_dimensions: Temporal context columns.
        facts: Quantitative, row-level values.
        metrics: Aggregated measures scoped to this table.
        filters: Predefined query conditions.
    """

    name: str = Field(
        ...,
        description="Unique identifier for the table",
    )
    synonyms: list[str] = Field(
        default_factory=list,
        description="Alternative terminology",
    )
    description: str | None = Field(
        default=None,
        description="Purpose and content details",
    )
    base_table: list[str] = Field(
        ...,
        description=(
            "Fully qualified database name components (e.g., ['catalog', 'schema', 'table'])"
        ),
    )
    primary_key: list[str] = Field(
        default_factory=list,
        description="Columns uniquely identifying rows (required for relationships)",
    )
    dimensions: list[Dimension] = Field(
        default_factory=list,
        description="Categorical columns",
    )
    time_dimensions: list[TimeDimension] = Field(
        default_factory=list,
        description="Temporal context columns",
    )
    facts: list[Fact] = Field(
        default_factory=list,
        description="Quantitative, row-level values",
    )
    metrics: list[Metric] = Field(
        default_factory=list,
        description="Aggregated measures",
    )
    filters: list[Filter] = Field(
        default_factory=list,
        description="Predefined query conditions",
    )

    @model_validator(mode="after")
    def validate_unique_column_names(self) -> Self:
        """Validate that all column names are unique within the table."""
        column_names: list[str] = []

        for dim in self.dimensions:
            column_names.append(dim.name)
        for time_dim in self.time_dimensions:
            column_names.append(time_dim.name)
        for fact in self.facts:
            column_names.append(fact.name)
        for metric in self.metrics:
            column_names.append(metric.name)

        seen: set[str] = set()
        duplicates: list[str] = []
        for name in column_names:
            if name in seen:
                duplicates.append(name)
            seen.add(name)

        if duplicates:
            raise ValueError(f"Duplicate column names found in table '{self.name}': {duplicates}")

        return self


class DatasetAttributes(BaseModel):
    """Attributes specific to a Dataset resource.

    Contains the semantic model definition following the Cortex Analyst spec.

    Attributes:
        description: Overview of the model's analytical purpose.
        tables: Collection of logical tables.
        relationships: Join definitions between tables.
        metrics: Derived metrics scoped to the semantic model.
        verified_queries: Example questions with verified SQL answers.
        custom_instructions: Business context guidance for LLM.
    """

    description: str | None = Field(
        default=None,
        description="Overview of the model's analytical purpose",
    )
    tables: list[Table] = Field(
        default_factory=list,
        description="Collection of logical tables",
    )
    relationships: list[Relationship] = Field(
        default_factory=list,
        description="Join definitions between tables",
    )
    metrics: list[Metric] = Field(
        default_factory=list,
        description="Derived metrics at semantic model level",
    )

    @model_validator(mode="after")
    def validate_unique_table_names(self) -> Self:
        """Validate that all table names are unique within the dataset."""
        table_names = [table.name for table in self.tables]

        seen: set[str] = set()
        duplicates: list[str] = []
        for name in table_names:
            if name in seen:
                duplicates.append(name)
            seen.add(name)

        if duplicates:
            raise ValueError(f"Duplicate table names found: {duplicates}")

        return self

    @model_validator(mode="after")
    def validate_unique_relationship_names(self) -> Self:
        """Validate that all relationship names are unique within the dataset."""
        relationship_names = [rel.name for rel in self.relationships]

        seen: set[str] = set()
        duplicates: list[str] = []
        for name in relationship_names:
            if name in seen:
                duplicates.append(name)
            seen.add(name)

        if duplicates:
            raise ValueError(f"Duplicate relationship names found: {duplicates}")

        return self


class Dataset(BaseResourceModel[DatasetAttributes, Literal["Dataset"]]):
    """A Dataset resource representing a semantic data model.

    Datasets follow the Snowflake Cortex Analyst Semantic Model Specification
    and provide a structured way to define logical tables, dimensions, facts,
    metrics, relationships, and verified queries for analytical queries.

    The Dataset model can be instantiated directly, from a dictionary, or loaded
    from JSON, YAML, or TOML files using the inherited file loader methods.

    Example:
        >>> # Direct instantiation
        >>> dataset = Dataset(
        ...     id="ds-001",
        ...     name="Sales Dataset",
        ...     slug="sales-dataset",
        ...     kind="Dataset",
        ...     attributes=DatasetAttributes(
        ...         description="Sales analytics dataset",
        ...         tables=[...]
        ...     )
        ... )

        >>> # From file
        >>> dataset = Dataset.from_yaml_file("path/to/dataset.yaml")

    Reference:
        https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/semantic-model-spec
    """

    kind: Literal["Dataset"] = Field(default="Dataset")
