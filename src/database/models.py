"""Pydantic models for database tables."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Customer(BaseModel):
    """Customer table model."""

    customer_id: int = Field(..., description="Unique customer identifier")
    customer_name: str = Field(..., description="Customer full name")
    email: str | None = Field(None, description="Email address (may be NULL)")
    phone: str | None = Field(None, description="Phone number (may be NULL)")
    country: str | None = Field(None, description="Customer country (may be NULL)")
    registration_date: date = Field(..., description="Account creation date")
    customer_segment: str = Field(
        ..., description="Customer tier (Premium, Standard, Basic, VIP)"
    )
    lifetime_value: Decimal = Field(..., description="Total customer spend")
    scope_date: date = Field(..., description="Date when this data was ingested/processed")


class Product(BaseModel):
    """Product table model."""

    product_id: int = Field(..., description="Unique product identifier")
    product_name: str | None = Field(None, description="Product name (may be NULL)")
    category: str = Field(..., description="Main product category")
    subcategory: str = Field(..., description="Product subcategory")
    unit_price: Decimal = Field(..., description="Selling price")
    cost_price: Decimal = Field(..., description="Cost of goods")
    supplier_id: int = Field(..., description="Supplier reference")
    stock_quantity: int = Field(..., description="Current inventory")
    reorder_level: int = Field(..., description="Reorder threshold")
    scope_date: date = Field(..., description="Date when this data was ingested/processed")


class SalesTransaction(BaseModel):
    """Sales transaction table model."""

    transaction_id: int = Field(..., description="Unique transaction identifier")
    customer_id: int = Field(..., description="Customer reference")
    product_id: int = Field(..., description="Product reference")
    transaction_date: date = Field(..., description="Transaction date")
    quantity: int = Field(..., description="Items purchased")
    unit_price: Decimal = Field(..., description="Price at time of sale")
    discount_percent: Decimal = Field(..., description="Discount applied")
    total_amount: Decimal = Field(..., description="Final transaction amount")
    payment_method: str | None = Field(
        None, description="Payment type (may be NULL)"
    )
    sales_channel: str = Field(
        ..., description="Sales channel (Online, Store, Mobile, Phone)"
    )
    region: str = Field(..., description="Sales region")
    scope_date: date = Field(..., description="Date when this data was ingested/processed")


class DataQualityMetric(BaseModel):
    """Data quality metrics table model."""

    metric_id: int = Field(..., description="Unique metric identifier")
    table_name: str = Field(..., description="Table being measured")
    metric_name: str = Field(
        ..., description="Metric type (completeness, accuracy, etc.)"
    )
    metric_value: Decimal = Field(..., description="Metric score (0-1)")
    calculation_date: datetime = Field(..., description="When metric was calculated")
    logic_date: date = Field(..., description="Date for which data is measured")
    status: str = Field(..., description="Calculation status (success, failed)")


class PipelineRun(BaseModel):
    """Pipeline run table model."""

    run_id: int = Field(..., description="Unique run identifier")
    pipeline_name: str = Field(..., description="Pipeline identifier")
    logic_date: date = Field(..., description="Date being processed")
    start_time: datetime = Field(..., description="Pipeline start time")
    end_time: datetime | None = Field(None, description="Pipeline end time")
    status: str = Field(..., description="Run status (success, failed, running)")
    records_processed: int = Field(..., description="Number of records processed")
    errors_count: int = Field(..., description="Number of errors encountered")
    run_by: str = Field(..., description="User or system that triggered run")
