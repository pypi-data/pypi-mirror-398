
"""
Tests for True Relational Integrity features:
1. Logic Gap (Conditional Foreign Keys)
2. Time Travel (Parent-Relative Dates)
"""

import pandas as pd
import pytest
from datetime import timedelta

from misata.schema import Column, Relationship, SchemaConfig, Table
from misata.simulator import DataSimulator


class TestIntegrity:
    """Tests for advanced integrity constraints."""
    
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
    def conditional_schema(self):
        """Schema with conditional foreign key logic (Logic Gap)."""
        return SchemaConfig(
            name="LogicGapTest",
            seed=42,
            tables=[
                Table(name="users", row_count=100),
                Table(name="orders", row_count=50),
            ],
            columns={
                "users": [
                    Column(name="id", type="int", distribution_params={"distribution": "uniform", "min": 1, "max": 100}, unique=True),
                    Column(name="status", type="categorical", distribution_params={"choices": ["active", "inactive", "banned"]}),
                ],
                "orders": [
                    Column(name="id", type="int", distribution_params={"distribution": "uniform", "min": 1, "max": 1000}),
                    Column(name="user_id", type="foreign_key", distribution_params={}),
                ]
            },
            relationships=[
                # Only link orders to ACTIVE users
                Relationship(
                    parent_table="users", 
                    child_table="orders", 
                    parent_key="id", 
                    child_key="user_id",
                    filters={"status": "active"} 
                )
            ]
        )

    @pytest.fixture
    def time_travel_schema(self):
        """Schema with parent-relative dates (Time Travel)."""
        return SchemaConfig(
            name="TimeTravelTest",
            seed=42,
            tables=[
                Table(name="projects", row_count=50),
                Table(name="tasks", row_count=200),
            ],
            columns={
                "projects": [
                    Column(name="id", type="int", distribution_params={"min": 1, "max": 1000}, unique=True),
                    Column(name="start_date", type="date", distribution_params={"start": "2023-01-01", "end": "2023-06-01"}),
                ],
                "tasks": [
                    Column(name="id", type="int", distribution_params={"min": 1, "max": 5000}),
                    Column(name="project_id", type="foreign_key", distribution_params={}),
                    Column(name="created_at", type="date", distribution_params={
                        "relative_to": "projects.start_date",  # Child date relative to parent date
                        "min_delta_days": 1,
                        "max_delta_days": 30
                    }),
                ]
            },
            relationships=[
                Relationship(parent_table="projects", child_table="tasks", parent_key="id", child_key="project_id")
            ]
        )

    def test_logic_gap_conditional_fk(self, conditional_schema):
        """
        Verify that orders are ONLY linked to 'active' users.
        This tests the Smart Context filtering logic.
        """
        simulator = DataSimulator(conditional_schema)
        data = self.generate_and_collect(simulator)
        
        users = data["users"]
        orders = data["orders"]
        
        # Join orders to users to check status of linked users
        merged = orders.merge(users, left_on="user_id", right_on="id", how="left")
        
        # Inspect statuses of linked users
        linked_statuses = merged["status"].unique()
        print(f"Linked User Statuses: {linked_statuses}")
        
        # Should ONLY contain 'active'
        assert set(linked_statuses) == {"active"}
        
        # Ensure we didn't just generate 0 rows
        assert len(orders) == 50

    def test_time_travel_relative_dates(self, time_travel_schema):
        """
        Verify that task.created_at is always AFTER project.start_date.
        This tests the Smart Context relative date generation logic.
        """
        simulator = DataSimulator(time_travel_schema)
        data = self.generate_and_collect(simulator)
        
        projects = data["projects"]
        tasks = data["tasks"]
        
        # Join tasks to projects to compare dates
        merged = tasks.merge(projects, left_on="project_id", right_on="id", suffixes=('_task', '_proj'))
        
        # Calculate delay
        merged["delay"] = merged["created_at"] - merged["start_date"]
        
        # Debug info
        print("\nDate Verification Sample:")
        print(merged[["start_date", "created_at", "delay"]].head())
        
        # Assert all tasks are created AFTER project start
        # min_delta_days was 1, so delay should be >= 1 day
        min_delay = merged["delay"].min()
        assert min_delay >= timedelta(days=1)
        
        # Assert max delay is within range (30 days)
        max_delay = merged["delay"].max()
        assert max_delay < timedelta(days=31)

