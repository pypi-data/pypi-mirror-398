from pygeai.migration.strategies import MigrationStrategy


class MigrationTool:

    def __init__(self, strategy: MigrationStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: MigrationStrategy):
        self.strategy = strategy

    def run_migration(self):
        self.strategy.migrate()
