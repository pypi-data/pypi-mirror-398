import unittest
from unittest.mock import Mock

from pygeai.migration.tools import MigrationTool
from pygeai.migration.strategies import MigrationStrategy


class TestMigrationTool(unittest.TestCase):
    """
    python -m unittest pygeai.tests.migration.test_tools.TestMigrationTool
    """

    def setUp(self):
        """Set up test fixtures"""
        self.mock_strategy = Mock(spec=MigrationStrategy)

    def test_migration_tool_initialization(self):
        """Test MigrationTool initialization with a strategy"""
        tool = MigrationTool(self.mock_strategy)
        self.assertEqual(tool.strategy, self.mock_strategy)

    def test_migration_tool_set_strategy(self):
        """Test setting a new strategy on MigrationTool"""
        tool = MigrationTool(self.mock_strategy)
        new_strategy = Mock(spec=MigrationStrategy)
        tool.set_strategy(new_strategy)

        self.assertEqual(tool.strategy, new_strategy)

    def test_migration_tool_run_migration(self):
        """Test running migration with the strategy"""
        tool = MigrationTool(self.mock_strategy)
        tool.run_migration()

        self.mock_strategy.migrate.assert_called_once()