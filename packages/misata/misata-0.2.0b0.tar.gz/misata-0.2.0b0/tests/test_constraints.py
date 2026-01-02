
"""
Tests for Business Rule Constraints.
"""

import pandas as pd
import pytest

from misata.schema import Column, Constraint, SchemaConfig, Table
from misata.simulator import DataSimulator


class TestConstraints:
    """Tests for business rule constraint enforcement."""
    
    def generate_and_collect(self, simulator):
        """Helper to consume generator and collect all data."""
        data = {}
        for table_name, batch_df in simulator.generate_all():
            if table_name in data:
                data[table_name] = pd.concat([data[table_name], batch_df], ignore_index=True)
            else:
                data[table_name] = batch_df
        return data

    @pytest.fixture
    def max_hours_schema(self):
        """Schema with max hours per employee per day constraint."""
        return SchemaConfig(
            name="TimesheetConstraintTest",
            seed=42,
            tables=[
                Table(
                    name="timesheets", 
                    row_count=100,
                    constraints=[
                        Constraint(
                            name="max_daily_hours",
                            type="max_per_group",
                            group_by=["employee_id", "date"],
                            column="hours",
                            value=8.0,
                            action="cap"
                        )
                    ]
                ),
            ],
            columns={
                "timesheets": [
                    Column(name="id", type="int", distribution_params={"min": 1, "max": 1000}),
                    Column(name="employee_id", type="int", distribution_params={"min": 1, "max": 10}),
                    Column(name="date", type="date", distribution_params={"start": "2024-01-01", "end": "2024-01-10"}),
                    Column(name="hours", type="float", distribution_params={"min": 1.0, "max": 12.0}),  # Intentionally can exceed 8
                ]
            },
            relationships=[]
        )

    @pytest.fixture
    def sum_limit_schema(self):
        """Schema with sum limit constraint (total hours per day)."""
        return SchemaConfig(
            name="SumLimitTest",
            seed=42,
            tables=[
                Table(
                    name="timesheets", 
                    row_count=50,
                    constraints=[
                        Constraint(
                            name="max_total_daily_hours",
                            type="sum_limit",
                            group_by=["employee_id", "date"],
                            column="hours",
                            value=8.0,
                            action="cap"
                        )
                    ]
                ),
            ],
            columns={
                "timesheets": [
                    Column(name="id", type="int", distribution_params={"min": 1, "max": 1000}),
                    Column(name="employee_id", type="int", distribution_params={"min": 1, "max": 5}),
                    Column(name="date", type="date", distribution_params={"start": "2024-01-01", "end": "2024-01-05"}),
                    Column(name="hours", type="float", distribution_params={"min": 1.0, "max": 6.0}),
                ]
            },
            relationships=[]
        )

    def test_max_per_group_constraint(self, max_hours_schema):
        """
        Verify that hours are capped at 8 per employee per day.
        """
        simulator = DataSimulator(max_hours_schema)
        data = self.generate_and_collect(simulator)
        
        timesheets = data["timesheets"]
        
        # Check max value per group
        max_hours = timesheets.groupby(["employee_id", "date"])["hours"].max()
        
        print(f"Max hours per group:\n{max_hours.head(10)}")
        
        # All should be <= 8
        assert max_hours.max() <= 8.0

    def test_sum_limit_constraint(self, sum_limit_schema):
        """
        Verify that total hours per employee per day <= 8.
        """
        simulator = DataSimulator(sum_limit_schema)
        data = self.generate_and_collect(simulator)
        
        timesheets = data["timesheets"]
        
        # Check sum per group
        total_hours = timesheets.groupby(["employee_id", "date"])["hours"].sum()
        
        print(f"Total hours per group:\n{total_hours.head(10)}")
        
        # All should be <= 8
        assert total_hours.max() <= 8.0
